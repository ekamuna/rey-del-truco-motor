"""Tests del AgentePIMC (inferencia) y de la restricción del envido."""

from dataclasses import replace

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.pimc import AgentePIMC, _consistente, _intervalos_prohibidos, _pozo
from truco.core.acciones import Accion, TipoAccion, canto
from truco.core.cards import Carta, Palo
from truco.core.engine import aplicar, iniciar, nueva_ronda, observacion_de
from truco.core.state import EstadoObservable, Negociacion, ResultadoBaza
from truco.evaluacion import enfrentar
from truco.game_loop import jugar_ronda


def _obs_respondiendo_envido(mi_mano: tuple[Carta, ...], mi_tanto: int) -> EstadoObservable:
    """Soy pie (jugador 1); el rival (mano) me cantó ENVIDO y debo responder."""
    return EstadoObservable(
        jugador=1,
        mi_mano=mi_mano,
        mano=0,
        turno=0,
        mesa=(None, None),
        bazas=(),
        cartas_rival=3,
        pendiente=Negociacion(categoria="envido", cantos=(TipoAccion.ENVIDO,), a_responder=1),
        nivel_truco=0,
        truco_querido=False,
        envido_resuelto=False,
        puntos_partida=(0, 0),
        objetivo=15,
        terminada=False,
        ganador=None,
        puntos_ronda=(0, 0),
        mi_tanto=mi_tanto,
        tanto_rival=None,
    )


MANO_28 = (Carta(5, Palo.ORO), Carta(3, Palo.ORO), Carta(1, Palo.COPA))  # tanto 28
MANO_27 = (Carta(7, Palo.COPA), Carta(11, Palo.COPA), Carta(10, Palo.ORO))  # tanto 27


def test_pimc_juega_legal() -> None:
    final = jugar_ronda(nueva_ronda(seed=3), (AgentePIMC(muestras=20), AgenteAleatorio(3)))
    assert final.terminada


def test_pimc_le_gana_holgado_al_azar() -> None:
    wr = enfrentar(
        lambda: AgentePIMC(muestras=30), lambda: AgenteAleatorio(2), partidas=40, seed=1
    ).winrate_a
    assert wr > 0.75


def test_tanto_del_mano_es_publico_tras_quiero() -> None:
    # j0 es mano (canta primero su número); j1 pie que pierde dice "son buenas".
    e = iniciar(MANO_28, MANO_27, mano=0)
    e = aplicar(e, canto(TipoAccion.ENVIDO))
    e = aplicar(e, canto(TipoAccion.QUIERO))
    assert observacion_de(e, 1).tanto_rival == 28  # j1 conoce el 28 del mano
    assert observacion_de(e, 0).tanto_rival is None  # j0 no conoce el del pie (son buenas)


def test_tanto_oculto_si_no_hubo_quiero() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    e = aplicar(e, canto(TipoAccion.ENVIDO))
    e = aplicar(e, canto(TipoAccion.NO_QUIERO))
    assert observacion_de(e, 1).tanto_rival is None


def test_restriccion_del_envido_sesga_el_muestreo() -> None:
    # Teoría del experto: cantó 28, mostró 2-copa y 7-oro → su tercera es 1-oro o 6-copa.
    obs = EstadoObservable(
        jugador=0,
        mi_mano=(Carta(4, Palo.BASTO),),
        mano=1,
        turno=0,
        mesa=(None, Carta(7, Palo.ORO)),  # el rival mostró el 7 de oro
        bazas=(ResultadoBaza(cartas=(Carta(4, Palo.ESPADA), Carta(2, Palo.COPA)), ganador=1),),
        cartas_rival=1,
        pendiente=None,
        nivel_truco=1,
        truco_querido=True,
        envido_resuelto=True,
        puntos_partida=(0, 0),
        objetivo=15,
        terminada=False,
        ganador=None,
        puntos_ronda=(0, 0),
        mi_tanto=20,
        tanto_rival=28,
    )
    posibles = {Carta(1, Palo.ORO), Carta(6, Palo.COPA)}
    ag = AgentePIMC(seed=0)
    pozo = _pozo(obs)
    con = sum(ag._muestrear_rival(obs, pozo)[0] in posibles for _ in range(60))
    sin = sum(
        ag._muestrear_rival(replace(obs, tanto_rival=None), pozo)[0] in posibles for _ in range(60)
    )
    assert con > sin  # con la restricción, adivina muchísimo mejor la tercera carta


def test_deduccion_con_que_me_mato() -> None:
    # Lideré la baza 1 con el 12 de espada (fuerza 6) y el rival me la ganó con el
    # 1 de basto (fuerza 12). Deducción: sus otras cartas NO están entre 6 y 12.
    obs = EstadoObservable(
        jugador=0,
        mi_mano=(Carta(11, Palo.ESPADA),),
        mano=0,
        turno=1,
        mesa=(None, None),
        bazas=(ResultadoBaza(cartas=(Carta(12, Palo.ESPADA), Carta(1, Palo.BASTO)), ganador=1),),
        cartas_rival=2,
        pendiente=None,
        nivel_truco=0,
        truco_querido=False,
        envido_resuelto=False,
        puntos_partida=(0, 0),
        objetivo=15,
        terminada=False,
        ganador=None,
        puntos_ronda=(0, 0),
        mi_tanto=20,
        tanto_rival=None,
    )
    intervalos = _intervalos_prohibidos(obs)
    assert intervalos == [(6, 12)]
    # una mano con un 2 (fuerza 8, entre el rey y el 1 de basto) es IMPOSIBLE
    assert not _consistente(obs, [Carta(2, Palo.ORO), Carta(4, Palo.COPA)], [], intervalos)
    # una mano con cartas flojas (fuerza < 6) sí es posible
    assert _consistente(obs, [Carta(5, Palo.ORO), Carta(4, Palo.COPA)], [], intervalos)


def _obs_respondiendo_carta(
    mi_mano: tuple[Carta, ...], carta_rival: Carta, bazas: tuple[ResultadoBaza, ...]
) -> EstadoObservable:
    """Jugador 0; el rival lideró la baza en curso con ``carta_rival`` y debo jugar."""
    return EstadoObservable(
        jugador=0,
        mi_mano=mi_mano,
        mano=1,
        turno=0,
        mesa=(None, carta_rival),
        bazas=bazas,
        cartas_rival=len(mi_mano),
        pendiente=None,
        nivel_truco=0,
        truco_querido=False,
        envido_resuelto=True,
        puntos_partida=(0, 0),
        objetivo=15,
        terminada=False,
        ganador=None,
        puntos_ronda=(0, 0),
        mi_tanto=20,
        tanto_rival=None,
    )


def test_emparda_en_baza1_en_vez_de_matar() -> None:
    # Mano: 1-basto (brava), 5-oro, 11-basto. Rival lidera la 1ª con 11-copa.
    # La política EMPARDA con el 11 (guarda la brava para la 2ª), no mata con el 1.
    obs = _obs_respondiendo_carta(
        (Carta(1, Palo.BASTO), Carta(5, Palo.ORO), Carta(11, Palo.BASTO)),
        Carta(11, Palo.COPA),
        bazas=(),
    )
    accion = AgentePIMC(seed=0)._elegir_carta(obs, list(obs.mi_mano))
    assert accion.carta == Carta(11, Palo.BASTO)


def test_gana_en_baza2_no_emparda() -> None:
    # En baza 2, si puedo ganar, GANO (no emparo): mato con la brava.
    obs = _obs_respondiendo_carta(
        (Carta(1, Palo.BASTO), Carta(11, Palo.BASTO)),
        Carta(11, Palo.COPA),
        bazas=(ResultadoBaza(cartas=(Carta(4, Palo.ORO), Carta(5, Palo.ORO)), ganador=1),),
    )
    accion = AgentePIMC(seed=0)._elegir_carta(obs, list(obs.mi_mano))
    assert accion.carta == Carta(1, Palo.BASTO)


def test_revira_el_envido_con_tanto_muy_fuerte() -> None:
    # Al aceptar un envido con un monstruo, el PIMC ESCALA para inflar el pozo.
    ag = AgentePIMC(seed=0)
    todos = {
        TipoAccion.QUIERO,
        TipoAccion.NO_QUIERO,
        TipoAccion.ENVIDO,
        TipoAccion.REAL_ENVIDO,
        TipoAccion.FALTA_ENVIDO,
    }
    una = (Carta(4, Palo.ORO),)

    def escala(tanto: int) -> TipoAccion:
        return ag._escalar_o_querer(_obs_respondiendo_envido(una, tanto), todos).tipo

    assert escala(33) is TipoAccion.FALTA_ENVIDO
    assert escala(30) is TipoAccion.REAL_ENVIDO
    assert escala(28) is TipoAccion.ENVIDO  # envido-envido (revira)
    assert escala(27) is TipoAccion.QUIERO


def test_escalar_envido_usa_falta_cerca_del_final() -> None:
    # FIX E (consciente del marcador): yendo GANANDO cerca del final, cantar REAL ENVIDO
    # arriesga 5 → si perdés le regalás el partido al rival. Hay que cantar FALTA (capa el
    # riesgo y gana igual). Yendo ATRÁS, en cambio, escalar normal (una real ganada te da vuelta).
    ag = AgentePIMC(seed=0)
    todos = {TipoAccion.QUIERO, TipoAccion.NO_QUIERO, TipoAccion.ENVIDO,
             TipoAccion.REAL_ENVIDO, TipoAccion.FALTA_ENVIDO}
    base = _obs_respondiendo_envido((Carta(4, Palo.ORO),), 30)  # jugador 1, tanto 30
    ganando = replace(base, puntos_partida=(10, 13))  # bot 13 va ganando; real (5) le da 15 al rival
    assert ag._escalar_o_querer(ganando, todos).tipo is TipoAccion.FALTA_ENVIDO
    atras = replace(base, puntos_partida=(13, 10))  # bot 10 va atrás → real normal (dar vuelta)
    assert ag._escalar_o_querer(atras, todos).tipo is TipoAccion.REAL_ENVIDO
    lejos = replace(base, puntos_partida=(2, 6))  # gana pero lejos: la falta es grande → real
    assert ag._escalar_o_querer(lejos, todos).tipo is TipoAccion.REAL_ENVIDO


def _obs_gane_primera(mi_mano: tuple[Carta, ...], cartas_rival: int) -> EstadoObservable:
    """Soy pie (jugador 1) y GANÉ la baza 1; me quedan ``mi_mano`` y el rival ``cartas_rival``.
    Estado típico para decidir si escalo un truco."""
    baza1 = ResultadoBaza(cartas=(Carta(4, Palo.BASTO), Carta(12, Palo.ORO)), ganador=1)
    return EstadoObservable(
        jugador=1, mi_mano=mi_mano, mano=0, turno=1, mesa=(None, None), bazas=(baza1,),
        cartas_rival=cartas_rival, pendiente=None, nivel_truco=1, truco_querido=True,
        envido_resuelto=True, puntos_partida=(0, 0), objetivo=15, terminada=False,
        ganador=None, puntos_ronda=(0, 0), mi_tanto=20, tanto_rival=None,
    )


def test_escala_truco_solo_con_carta_casi_imbatible() -> None:
    # Teoría del experto: escalar (vale4) SÓLO con >90% seguro = a lo sumo 1 carta sin ver
    # me gana, y con estructura de 2 bazas. Con el MACHO (nada lo gana) escala; con basura
    # (un 4, que todo supera) NO escala aunque la prob sea alta (mata el farol de vale4).
    ag = AgentePIMC()
    subible = {TipoAccion.QUIERO, TipoAccion.NO_QUIERO, TipoAccion.RETRUCO}
    con_macho = _obs_gane_primera((Carta(1, Palo.ESPADA), Carta(5, Palo.ORO)), cartas_rival=2)
    assert ag._escalar_o_querer_truco(con_macho, subible, 0.90).tipo is TipoAccion.RETRUCO
    con_basura = _obs_gane_primera((Carta(4, Palo.ORO), Carta(5, Palo.ORO)), cartas_rival=2)
    assert ag._escalar_o_querer_truco(con_basura, subible, 0.90).tipo is TipoAccion.QUIERO
    # con prob baja tampoco escala (aun con el macho); y sin subida disponible, quiere
    assert ag._escalar_o_querer_truco(con_macho, subible, 0.50).tipo is TipoAccion.QUIERO
    assert ag._escalar_o_querer_truco(con_macho, {TipoAccion.QUIERO}, 0.90).tipo is TipoAccion.QUIERO


def test_estructura_para_cantar_exige_dos_bazas() -> None:
    # El truco se gana con 2 bazas: en baza 1 exijo 2 cartas fuertes; 1 carta+basura NO.
    ag = AgentePIMC()
    dos_fuertes = _obs_liderando((Carta(3, Palo.ESPADA), Carta(2, Palo.COPA), Carta(5, Palo.ORO)))
    assert ag._estructura_para_cantar_truco(dos_fuertes)  # 3(f9)+2(f8) = dos ganadores
    una_fuerte = _obs_liderando((Carta(7, Palo.ORO), Carta(6, Palo.COPA), Carta(12, Palo.COPA)))
    assert not ag._estructura_para_cantar_truco(una_fuerte)  # 7oro + basura → NO canto
    # gané la 1ª y me queda una carta fuerte → sí (1-0 con segunda buena)
    uno_cero = _obs_gane_primera((Carta(3, Palo.ESPADA), Carta(5, Palo.ORO)), cartas_rival=2)
    assert ag._estructura_para_cantar_truco(uno_cero)


def test_lidera_mas_alta_en_baza_decisiva_tras_parda() -> None:
    # FIX D: tras una parda, la baza que lidero DEFINE la mano → liderar la MÁS ALTA (no la
    # más baja). Escenario R12: parda en baza 1, lidero baza 2 con {12o, 6b} → debe ir el 12o.
    ag = AgentePIMC()
    parda = ResultadoBaza(cartas=(Carta(1, Palo.COPA), Carta(1, Palo.ORO)), ganador=None)
    base = _obs_gane_primera((Carta(12, Palo.ORO), Carta(6, Palo.BASTO)), cartas_rival=2)
    obs = replace(base, jugador=0, mano=0, bazas=(parda,), nivel_truco=0, truco_querido=False)
    assert ag._liderar(obs, [Carta(12, Palo.ORO), Carta(6, Palo.BASTO)]).carta == Carta(12, Palo.ORO)
    # control: baza 2 SIN parda (gané la 1ª) → slow-play, la más baja (comportamiento previo)
    gane = ResultadoBaza(cartas=(Carta(4, Palo.ORO), Carta(11, Palo.COPA)), ganador=0)
    obs2 = replace(obs, bazas=(gane,))
    assert ag._liderar(obs2, [Carta(12, Palo.ORO), Carta(6, Palo.BASTO)]).carta == Carta(6, Palo.BASTO)


def test_p_rival_supera_cuenta_las_que_ganan() -> None:
    ag = AgentePIMC()
    obs = _obs_gane_primera((Carta(1, Palo.ESPADA), Carta(5, Palo.ORO)), cartas_rival=2)
    assert ag._p_rival_supera(obs, Carta(1, Palo.ESPADA)) == 0.0  # nada supera al macho
    # a un 3 lo superan 4 cartas (7oro/7esp/hembra/macho) → prob > 0 (y bastante)
    assert ag._p_rival_supera(obs, Carta(3, Palo.ORO)) > 0.10


def _obs_liderando(mi_mano: tuple[Carta, ...]) -> EstadoObservable:
    """Jugador 0 lidera la baza 1 (nadie tiró todavía)."""
    return EstadoObservable(
        jugador=0,
        mi_mano=mi_mano,
        mano=0,
        turno=0,
        mesa=(None, None),
        bazas=(),
        cartas_rival=len(mi_mano),
        pendiente=None,
        nivel_truco=0,
        truco_querido=False,
        envido_resuelto=True,
        puntos_partida=(0, 0),
        objetivo=15,
        terminada=False,
        ganador=None,
        puntos_ronda=(0, 0),
        mi_tanto=20,
        tanto_rival=None,
    )


def test_lidera_hacer_primera_con_mano_floja() -> None:
    # Todas fuerza < 8 → liderar la MÁS ALTA (hacer primera; gana la 3ª por parda).
    obs = _obs_liderando((Carta(11, Palo.BASTO), Carta(4, Palo.COPA), Carta(5, Palo.ORO)))
    accion = AgentePIMC(seed=0)._elegir_carta(obs, list(obs.mi_mano))
    assert accion.carta == Carta(11, Palo.BASTO)  # fuerza 5, la más alta


def test_lidera_slow_play_con_carta_fuerte() -> None:
    # Con una carta fuerte (2♠ fuerza 8) → liderar la MÁS BAJA (guardar la fuerte).
    obs = _obs_liderando((Carta(2, Palo.ESPADA), Carta(4, Palo.COPA), Carta(5, Palo.ORO)))
    accion = AgentePIMC(seed=0)._elegir_carta(obs, list(obs.mi_mano))
    assert accion.carta == Carta(4, Palo.COPA)  # fuerza 0, la más baja


def test_umbral_aceptar_truco_es_break_even_del_nivel() -> None:
    # Break-even EV de aceptar: truco 0.25, retruco 0.5-2/6, vale cuatro 0.5-3/8.
    ag = AgentePIMC()

    def umbral(ultimo: TipoAccion) -> float:
        obs = _obs_respondiendo_envido((Carta(4, Palo.ORO),), 20)
        neg = Negociacion(categoria="truco", cantos=(ultimo,), a_responder=1)
        obs = replace(obs, pendiente=neg)
        return ag._umbral_querer_truco_ev(obs)

    assert abs(umbral(TipoAccion.TRUCO) - 0.25) < 1e-9
    assert abs(umbral(TipoAccion.RETRUCO) - (0.5 - 2 / 6)) < 1e-9
    assert abs(umbral(TipoAccion.VALE_CUATRO) - (0.5 - 3 / 8)) < 1e-9


def test_umbral_aceptar_envido_es_break_even_del_pote() -> None:
    # Un envido simple querido vale 2; el 'no quiero' regala 1 → break-even eq = 0.25.
    obs = _obs_respondiendo_envido((Carta(4, Palo.ORO),), mi_tanto=20)
    assert abs(AgentePIMC()._umbral_querer_envido_ev(obs) - 0.25) < 1e-9


def test_piso_selecciona_manos_altas_del_rival() -> None:
    # Al responder un envido, el rival cantó → sólo imagino manos suyas con tanto alto.
    obs = _obs_respondiendo_envido((Carta(3, Palo.ORO),), mi_tanto=24)
    ag = AgentePIMC(seed=0, tanto_rival_canta_envido=26)
    assert ag._piso_tanto_rival(obs) == 26  # envido simple → piso base


def test_no_pago_envido_flojo_pero_si_uno_fuerte() -> None:
    # De pie, el rival (mano) me canta envido. Con 24 debo NO querer (asumo que tiene
    # puntos: canta con >=26); con 31 debo querer.
    ag = AgentePIMC(seed=0, tanto_rival_canta_envido=26)
    m_flojo = (Carta(3, Palo.ORO), Carta(1, Palo.ORO), Carta(12, Palo.BASTO))  # tanto 24
    m_fuerte = (Carta(7, Palo.ORO), Carta(4, Palo.ORO), Carta(12, Palo.BASTO))  # tanto 31
    flojo = _obs_respondiendo_envido(m_flojo, 24)
    fuerte = _obs_respondiendo_envido(m_fuerte, 31)
    acciones = (Accion(TipoAccion.QUIERO), Accion(TipoAccion.NO_QUIERO))
    assert ag.actuar(flojo, acciones).tipo is TipoAccion.NO_QUIERO
    assert ag.actuar(fuerte, acciones).tipo is TipoAccion.QUIERO
