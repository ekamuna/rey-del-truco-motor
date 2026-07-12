"""Tests del motor de la ronda y la resolución de bazas (REGLAMENTO §3).

Cada fila de la tabla de pardas tiene su test. Las manos se construyen a mano
(con ``iniciar``) para que los escenarios sean deterministas.
"""

from collections.abc import Iterable

import pytest

from truco.core.acciones import TipoAccion, jugar_carta
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, aplicar, iniciar, nueva_ronda, observacion_de
from truco.core.state import EstadoRonda

MACHO = Carta(1, Palo.ESPADA)
BASTO = Carta(1, Palo.BASTO)
TRES_ORO = Carta(3, Palo.ORO)
TRES_COPA = Carta(3, Palo.COPA)
CUATRO_ESP = Carta(4, Palo.ESPADA)
CUATRO_ORO = Carta(4, Palo.ORO)
CINCO_ESP = Carta(5, Palo.ESPADA)
CINCO_ORO = Carta(5, Palo.ORO)
SEIS_ESP = Carta(6, Palo.ESPADA)
SEIS_ORO = Carta(6, Palo.ORO)


def jugar_cartas(estado: EstadoRonda, cartas: Iterable[Carta]) -> EstadoRonda:
    for carta in cartas:
        estado = aplicar(estado, jugar_carta(carta))
    return estado


# --- Reparto -----------------------------------------------------------------


def test_reparto_reproducible_por_seed() -> None:
    assert nueva_ronda(seed=42).manos == nueva_ronda(seed=42).manos


def test_reparto_tres_cartas_disjuntas() -> None:
    m0, m1 = nueva_ronda(seed=7).manos
    assert len(m0) == 3 and len(m1) == 3
    assert set(m0).isdisjoint(set(m1))


# --- Mecánica ----------------------------------------------------------------


def test_jugar_saca_la_carta_y_pasa_el_turno() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (BASTO, CUATRO_ESP, CINCO_ORO), mano=0)
    estado = aplicar(estado, jugar_carta(MACHO))
    assert MACHO not in estado.manos[0]
    assert estado.turno == 1


def test_acciones_legales_incluyen_las_cartas_de_la_mano() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (BASTO, CUATRO_ESP, CINCO_ORO), mano=0)
    jugables = {a.carta for a in acciones_legales(estado) if a.tipo is TipoAccion.JUGAR}
    assert jugables == {MACHO, CUATRO_ORO, CINCO_ESP}


def test_jugar_carta_que_no_se_tiene_falla() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (BASTO, CUATRO_ESP, CINCO_ORO), mano=0)
    with pytest.raises(ValueError):
        aplicar(estado, jugar_carta(BASTO))


def test_no_se_puede_jugar_en_ronda_terminada() -> None:
    estado = iniciar((MACHO, BASTO, CUATRO_ORO), (CUATRO_ESP, CINCO_ORO, SEIS_ORO), mano=0)
    estado = jugar_cartas(estado, [MACHO, CUATRO_ESP, BASTO, CINCO_ORO])
    assert estado.terminada
    with pytest.raises(RuntimeError):
        aplicar(estado, jugar_carta(CUATRO_ORO))


def test_observacion_oculta_la_mano_del_rival() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (BASTO, CUATRO_ESP, CINCO_ORO), mano=0)
    obs = observacion_de(estado, 0)
    assert obs.mi_mano == (MACHO, CUATRO_ORO, CINCO_ESP)
    assert obs.cartas_rival == 3
    assert obs.soy_mano is True
    assert not hasattr(obs, "manos")


# --- Tabla de pardas ---------------------------------------------------------


def test_gana_dos_bazas_seguidas() -> None:
    estado = iniciar((MACHO, BASTO, CUATRO_ORO), (CUATRO_ESP, CINCO_ORO, SEIS_ORO), mano=0)
    estado = jugar_cartas(estado, [MACHO, CUATRO_ESP, BASTO, CINCO_ORO])
    assert estado.terminada and estado.ganador == 0
    assert len(estado.bazas) == 2


def test_gana_primera_emparda_segunda() -> None:
    estado = iniciar((MACHO, TRES_ORO, CUATRO_ORO), (CUATRO_ESP, TRES_COPA, SEIS_ORO), mano=0)
    estado = jugar_cartas(estado, [MACHO, CUATRO_ESP, TRES_ORO, TRES_COPA])
    assert estado.terminada and estado.ganador == 0


def test_emparda_primera_gana_segunda() -> None:
    estado = iniciar((CUATRO_ESP, CINCO_ESP, SEIS_ESP), (CUATRO_ORO, MACHO, SEIS_ORO), mano=0)
    estado = jugar_cartas(estado, [CUATRO_ESP, CUATRO_ORO, CINCO_ESP, MACHO])
    assert estado.terminada and estado.ganador == 1


def test_uno_a_uno_tercera_parda_gana_quien_gano_la_primera() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (CUATRO_ESP, BASTO, CINCO_ORO), mano=0)
    estado = jugar_cartas(estado, [MACHO, CUATRO_ESP, CUATRO_ORO, BASTO, CINCO_ORO, CINCO_ESP])
    assert estado.terminada and estado.ganador == 0
    assert len(estado.bazas) == 3


def test_todas_pardas_gana_el_mano() -> None:
    estado = iniciar((CUATRO_ESP, CINCO_ESP, SEIS_ESP), (CUATRO_ORO, CINCO_ORO, SEIS_ORO), mano=1)
    estado = jugar_cartas(
        estado, [CUATRO_ORO, CUATRO_ESP, CINCO_ORO, CINCO_ESP, SEIS_ORO, SEIS_ESP]
    )
    assert estado.terminada and estado.ganador == 1
    assert all(b.ganador is None for b in estado.bazas)


def test_parda_primera_arranca_el_mano_la_segunda() -> None:
    estado = iniciar((CUATRO_ESP, MACHO, SEIS_ESP), (CUATRO_ORO, BASTO, SEIS_ORO), mano=0)
    estado = jugar_cartas(estado, [CUATRO_ESP, CUATRO_ORO])
    assert estado.turno == 0


def test_ganar_las_bazas_sin_truco_vale_1() -> None:
    estado = iniciar((MACHO, BASTO, CUATRO_ORO), (CUATRO_ESP, CINCO_ORO, SEIS_ORO), mano=0)
    estado = jugar_cartas(estado, [MACHO, CUATRO_ESP, BASTO, CINCO_ORO])
    assert estado.puntos_ronda == (1, 0)
