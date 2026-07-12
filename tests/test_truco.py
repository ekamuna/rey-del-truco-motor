"""Tests del truco cantado y de "el envido está primero" (REGLAMENTO §5, §6)."""

from collections.abc import Iterable

from truco.core.acciones import TipoAccion, canto, jugar_carta
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, aplicar, iniciar, observacion_de
from truco.core.state import EstadoRonda

MACHO = Carta(1, Palo.ESPADA)
BASTO = Carta(1, Palo.BASTO)
CUATRO_ESP = Carta(4, Palo.ESPADA)
CUATRO_ORO = Carta(4, Palo.ORO)
CINCO_ORO = Carta(5, Palo.ORO)
SEIS_ORO = Carta(6, Palo.ORO)

# j0 gana 2-0 con dos bravas.
G0 = (MACHO, BASTO, CUATRO_ESP)
G1 = (CUATRO_ORO, CINCO_ORO, SEIS_ORO)
# Manos con tanto para el test de "envido primero" (j0 28, j1 27).
E0 = (Carta(5, Palo.ORO), Carta(3, Palo.ORO), Carta(1, Palo.COPA))
E1 = (Carta(7, Palo.COPA), Carta(11, Palo.COPA), Carta(10, Palo.ORO))


def jugar_cartas(estado: EstadoRonda, cartas: Iterable[Carta]) -> EstadoRonda:
    for c in cartas:
        estado = aplicar(estado, jugar_carta(c))
    return estado


def test_truco_querido_vale_2() -> None:
    e = iniciar(G0, G1, mano=0)
    e = aplicar(e, canto(TipoAccion.TRUCO))
    e = aplicar(e, canto(TipoAccion.QUIERO))
    assert e.truco_querido and e.nivel_truco == 1
    e = jugar_cartas(e, [MACHO, CUATRO_ORO, BASTO, CINCO_ORO])
    assert e.terminada and e.puntos_ronda == (2, 0)


def test_truco_no_querido_da_1_al_cantor() -> None:
    e = iniciar(G0, G1, mano=0)
    e = aplicar(e, canto(TipoAccion.TRUCO))
    e = aplicar(e, canto(TipoAccion.NO_QUIERO))
    assert e.terminada and e.ganador == 0 and e.puntos_ronda == (1, 0)


def test_retruco_querido_vale_3() -> None:
    e = iniciar(G0, G1, mano=0)
    e = aplicar(e, canto(TipoAccion.TRUCO))  # j0
    e = aplicar(e, canto(TipoAccion.RETRUCO))  # j1 sube
    e = aplicar(e, canto(TipoAccion.QUIERO))  # j0 quiere
    assert e.nivel_truco == 2 and e.puede_subir_truco == 0
    e = jugar_cartas(e, [MACHO, CUATRO_ORO, BASTO, CINCO_ORO])
    assert e.puntos_ronda == (3, 0)


def test_vale_cuatro_no_querido_da_3() -> None:
    e = iniciar(G0, G1, mano=0)
    e = aplicar(e, canto(TipoAccion.TRUCO))  # j0
    e = aplicar(e, canto(TipoAccion.RETRUCO))  # j1
    e = aplicar(e, canto(TipoAccion.QUIERO))  # j0 quiere (nivel 2)
    e = aplicar(e, canto(TipoAccion.VALE_CUATRO))  # j0 sube en su turno
    e = aplicar(e, canto(TipoAccion.NO_QUIERO))  # j1 no quiere
    assert e.terminada and e.ganador == 0 and e.puntos_ronda == (3, 0)


def test_irse_al_mazo_da_los_puntos_al_rival() -> None:
    e = iniciar(G0, G1, mano=0)
    e = aplicar(e, canto(TipoAccion.MAZO))  # j0 abandona
    assert e.terminada and e.ganador == 1 and e.puntos_ronda == (0, 1)


def test_envido_esta_primero() -> None:
    e = iniciar(E0, E1, mano=0)
    e = aplicar(e, canto(TipoAccion.TRUCO))  # j0 canta truco sin jugar carta
    assert e.pendiente is not None and e.pendiente.categoria == "truco"
    # j1 puede responder con envido (envido primero)
    assert TipoAccion.ENVIDO in {a.tipo for a in acciones_legales(e)}
    e = aplicar(e, canto(TipoAccion.ENVIDO))  # j1 canta envido
    assert e.truco_suspendido is not None
    assert e.pendiente is not None and e.pendiente.categoria == "envido"
    e = aplicar(e, canto(TipoAccion.QUIERO))  # j0 quiere el envido
    assert e.envido_resuelto and e.puntos_ronda == (2, 0)  # j0 (28) gana el envido
    # el truco vuelve a estar pendiente, ahora responde j1
    assert e.pendiente is not None and e.pendiente.categoria == "truco"
    assert e.pendiente.a_responder == 1
    e = aplicar(e, canto(TipoAccion.QUIERO))  # j1 quiere el truco
    assert e.truco_querido


def test_observacion_con_mano_vacia_no_rompe() -> None:
    # Regresión: cantar truco en la última baza obliga a responder al que ya
    # jugó todas sus cartas; su observación no debe romperse.
    e = iniciar(
        (MACHO, CUATRO_ORO, Carta(5, Palo.ESPADA)),
        (CUATRO_ESP, BASTO, Carta(5, Palo.ORO)),
        mano=0,
    )
    e = jugar_cartas(e, [MACHO, CUATRO_ESP, CUATRO_ORO, BASTO])  # 1-1 tras dos bazas
    e = aplicar(e, jugar_carta(Carta(5, Palo.ORO)))  # j1 juega su última carta (queda vacío)
    e = aplicar(e, canto(TipoAccion.TRUCO))  # j0 canta; j1 (mano vacía) debe responder
    obs = observacion_de(e, 1)
    assert obs.mi_mano == ()
    assert obs.mi_tanto == e.tantos[1]  # el tanto original, no recalculado
