"""Tests del AgentePIMC (inferencia) y de la restricción del envido."""

from dataclasses import replace

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.pimc import AgentePIMC, _consistente, _intervalos_prohibidos, _pozo
from truco.core.acciones import TipoAccion, canto
from truco.core.cards import Carta, Palo
from truco.core.engine import aplicar, iniciar, nueva_ronda, observacion_de
from truco.core.state import EstadoObservable, ResultadoBaza
from truco.evaluacion import enfrentar
from truco.game_loop import jugar_ronda

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
