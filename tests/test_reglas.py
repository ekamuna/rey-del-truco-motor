"""Tests de las heurísticas del AgenteReglas (M4/M5)."""

from truco.agents.reglas import AgenteReglas, ConfigReglas
from truco.core.acciones import Accion, TipoAccion, canto, jugar_carta
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, aplicar, iniciar, observacion_de
from truco.core.state import EstadoRonda

# j0 con envido alto (28) y dos bravas; j1 flojo.
FUERTE = (Carta(1, Palo.ESPADA), Carta(7, Palo.ESPADA), Carta(6, Palo.ESPADA))  # tanto 33
DEBIL = (Carta(4, Palo.ORO), Carta(5, Palo.COPA), Carta(6, Palo.BASTO))  # tanto 6


def _decidir(estado: EstadoRonda, jugador: int) -> Accion:
    bot = AgenteReglas()
    return bot.actuar(observacion_de(estado, jugador), acciones_legales(estado))


def test_canta_envido_con_tanto_alto() -> None:
    e = iniciar(FUERTE, DEBIL, mano=0)
    accion = _decidir(e, 0)
    assert accion.tipo in (TipoAccion.ENVIDO, TipoAccion.REAL_ENVIDO)


def test_no_canta_envido_con_tanto_bajo() -> None:
    e = iniciar(DEBIL, FUERTE, mano=0)  # j0 es mano pero tiene tanto 6
    accion = _decidir(e, 0)
    assert accion.tipo not in (TipoAccion.ENVIDO, TipoAccion.REAL_ENVIDO, TipoAccion.FALTA_ENVIDO)


def test_quiere_envido_con_buen_tanto() -> None:
    e = iniciar(FUERTE, DEBIL, mano=1)  # j1 es mano y canta; j0 responde
    e = aplicar(e, canto(TipoAccion.ENVIDO))  # lo canta j1 (mano)
    accion = _decidir(e, 0)  # j0 (tanto 33) responde
    assert accion.tipo in (TipoAccion.QUIERO, TipoAccion.REAL_ENVIDO)


def test_no_quiere_envido_con_tanto_bajo() -> None:
    e = iniciar(FUERTE, DEBIL, mano=0)
    e = aplicar(e, canto(TipoAccion.ENVIDO))  # j0 canta
    accion = _decidir(e, 1)  # j1 (tanto 6) responde
    assert accion.tipo is TipoAccion.NO_QUIERO


def test_no_quiere_truco_con_mano_muy_debil() -> None:
    e = iniciar(DEBIL, FUERTE, mano=1)  # j1 mano y fuerte, canta truco; j0 débil responde
    e = aplicar(e, canto(TipoAccion.TRUCO))  # j1 canta
    accion = _decidir(e, 0)  # j0 débil
    assert accion.tipo is TipoAccion.NO_QUIERO


def test_umbrales_configurables() -> None:
    # Con un umbral altísimo, no canta envido ni con 33.
    bot = AgenteReglas(ConfigReglas(cantar_envido=99))
    e = iniciar(FUERTE, DEBIL, mano=0)
    accion = bot.actuar(observacion_de(e, 0), acciones_legales(e))
    assert accion.tipo not in (TipoAccion.ENVIDO, TipoAccion.REAL_ENVIDO)


def test_elige_carta_minima_que_gana() -> None:
    # j1 (mano) juega el 5 de copa; el bot j0 debe ganarlo con la mínima
    # suficiente (el 6), sin malgastar el 3. (Mano sin bravas ni tanto para
    # que no cante truco ni envido y decida solo con la carta.)
    j0 = (Carta(6, Palo.ORO), Carta(3, Palo.COPA), Carta(4, Palo.BASTO))
    e = iniciar(j0, DEBIL, mano=1)
    e = aplicar(e, jugar_carta(Carta(5, Palo.COPA)))  # DEBIL[1] = 5 de copa
    accion = _decidir(e, 0)
    assert accion.tipo is TipoAccion.JUGAR
    assert accion.carta == Carta(6, Palo.ORO)
