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


def test_escala_truco_con_mano_casi_ganada() -> None:
    # Al querer un truco con prob muy alta, escala a retruco (valor); si no, quiere.
    ag = AgentePIMC()
    obs = _obs_respondiendo_envido((Carta(4, Palo.ORO),), 20)
    neg = Negociacion(categoria="truco", cantos=(TipoAccion.TRUCO,), a_responder=1)
    obs = replace(obs, pendiente=neg)
    subible = {TipoAccion.QUIERO, TipoAccion.NO_QUIERO, TipoAccion.RETRUCO}
    assert ag._escalar_o_querer_truco(obs, subible, 0.90).tipo is TipoAccion.RETRUCO
    assert ag._escalar_o_querer_truco(obs, subible, 0.50).tipo is TipoAccion.QUIERO
    # sin subida disponible, simplemente quiere
    assert ag._escalar_o_querer_truco(obs, {TipoAccion.QUIERO}, 0.90).tipo is TipoAccion.QUIERO


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
