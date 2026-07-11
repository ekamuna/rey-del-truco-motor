"""Tests del motor de la ronda y la resolución de bazas (REGLAMENTO §3).

Cada fila de la tabla de pardas tiene su test. Las manos se construyen a mano
(con ``iniciar``) para que los escenarios sean deterministas.
"""

from collections.abc import Iterable

import pytest

from truco.core.cards import Carta, Palo
from truco.core.engine import (
    acciones_legales,
    iniciar,
    jugar,
    nueva_ronda,
    observacion_de,
)
from truco.core.state import EstadoRonda

# Atajos de cartas útiles (fuerza de mayor a menor).
MACHO = Carta(1, Palo.ESPADA)  # la más fuerte
BASTO = Carta(1, Palo.BASTO)  # 2ª más fuerte
TRES_ORO = Carta(3, Palo.ORO)
TRES_COPA = Carta(3, Palo.COPA)
CUATRO_ESP = Carta(4, Palo.ESPADA)
CUATRO_ORO = Carta(4, Palo.ORO)
CINCO_ESP = Carta(5, Palo.ESPADA)
CINCO_ORO = Carta(5, Palo.ORO)
SEIS_ESP = Carta(6, Palo.ESPADA)
SEIS_ORO = Carta(6, Palo.ORO)


def jugar_secuencia(estado: EstadoRonda, cartas: Iterable[Carta]) -> EstadoRonda:
    """Juega una lista de cartas en orden, cada una por el jugador de turno."""
    for carta in cartas:
        estado = jugar(estado, carta)
    return estado


# --- Reparto -----------------------------------------------------------------


def test_reparto_reproducible_por_seed() -> None:
    a = nueva_ronda(seed=42)
    b = nueva_ronda(seed=42)
    assert a.manos == b.manos


def test_reparto_tres_cartas_disjuntas() -> None:
    estado = nueva_ronda(seed=7)
    m0, m1 = estado.manos
    assert len(m0) == 3
    assert len(m1) == 3
    assert set(m0).isdisjoint(set(m1))  # nadie comparte carta


# --- Mecánica de jugar -------------------------------------------------------


def test_jugar_saca_la_carta_y_pasa_el_turno() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (BASTO, CUATRO_ESP, CINCO_ORO), mano=0)
    assert estado.turno == 0
    estado = jugar(estado, MACHO)
    assert MACHO not in estado.manos[0]
    assert estado.turno == 1  # ahora le toca al rival


def test_acciones_legales_son_las_cartas_del_turno() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (BASTO, CUATRO_ESP, CINCO_ORO), mano=0)
    assert set(acciones_legales(estado)) == {MACHO, CUATRO_ORO, CINCO_ESP}


def test_jugar_carta_que_no_se_tiene_falla() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (BASTO, CUATRO_ESP, CINCO_ORO), mano=0)
    with pytest.raises(ValueError):
        jugar(estado, BASTO)  # esa carta es del rival


def test_no_se_puede_jugar_en_ronda_terminada() -> None:
    estado = iniciar((MACHO, BASTO, CUATRO_ORO), (CUATRO_ESP, CINCO_ORO, SEIS_ORO), mano=0)
    estado = jugar_secuencia(estado, [MACHO, CUATRO_ESP, BASTO, CINCO_ORO])  # 2-0 para j0
    assert estado.terminada
    with pytest.raises(RuntimeError):
        jugar(estado, CUATRO_ORO)


# --- Estado observable -------------------------------------------------------


def test_observacion_oculta_la_mano_del_rival() -> None:
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (BASTO, CUATRO_ESP, CINCO_ORO), mano=0)
    obs = observacion_de(estado, 0)
    assert obs.mi_mano == (MACHO, CUATRO_ORO, CINCO_ESP)
    assert obs.cartas_rival == 3  # sé cuántas tiene, no cuáles
    assert obs.soy_mano is True
    assert not hasattr(obs, "manos")  # no hay acceso al estado completo


# --- Tabla de pardas (REGLAMENTO §3) -----------------------------------------


def test_gana_dos_bazas_seguidas() -> None:
    # j0 gana baza 1 y 2 → gana la ronda 2-0 (no se juega la 3ª).
    estado = iniciar((MACHO, BASTO, CUATRO_ORO), (CUATRO_ESP, CINCO_ORO, SEIS_ORO), mano=0)
    estado = jugar_secuencia(estado, [MACHO, CUATRO_ESP, BASTO, CINCO_ORO])
    assert estado.terminada
    assert estado.ganador == 0
    assert len(estado.bazas) == 2


def test_gana_primera_emparda_segunda() -> None:
    # j0 gana la 1ª; en la 2ª empardan (dos treses) → gana j0.
    estado = iniciar((MACHO, TRES_ORO, CUATRO_ORO), (CUATRO_ESP, TRES_COPA, SEIS_ORO), mano=0)
    estado = jugar_secuencia(estado, [MACHO, CUATRO_ESP, TRES_ORO, TRES_COPA])
    assert estado.terminada
    assert estado.ganador == 0
    assert len(estado.bazas) == 2


def test_emparda_primera_gana_segunda() -> None:
    # Baza 1 parda (dos cuatros); baza 2 la gana j1 → gana j1.
    estado = iniciar((CUATRO_ESP, CINCO_ESP, SEIS_ESP), (CUATRO_ORO, MACHO, SEIS_ORO), mano=0)
    # Baza1: j0 CUATRO_ESP, j1 CUATRO_ORO → parda. Arranca el mano (j0) la baza2.
    # Baza2: j0 CINCO_ESP, j1 MACHO → gana j1.
    estado = jugar_secuencia(estado, [CUATRO_ESP, CUATRO_ORO, CINCO_ESP, MACHO])
    assert estado.terminada
    assert estado.ganador == 1


def test_uno_a_uno_tercera_parda_gana_quien_gano_la_primera() -> None:
    # j0 gana la 1ª, j1 gana la 2ª (1-1), la 3ª es parda → gana j0 (ganó la 1ª).
    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (CUATRO_ESP, BASTO, CINCO_ORO), mano=0)
    # Baza1: j0 MACHO vs j1 CUATRO_ESP → gana j0. Líder j0.
    # Baza2: j0 CUATRO_ORO vs j1 BASTO → gana j1. Líder j1.
    # Baza3: j1 CINCO_ORO vs j0 CINCO_ESP → parda.
    estado = jugar_secuencia(estado, [MACHO, CUATRO_ESP, CUATRO_ORO, BASTO, CINCO_ORO, CINCO_ESP])
    assert estado.terminada
    assert estado.ganador == 0
    assert len(estado.bazas) == 3


def test_todas_pardas_gana_el_mano() -> None:
    # Las 3 bazas pardas → gana el mano. Probamos que el mano manda (mano=1).
    estado = iniciar((CUATRO_ESP, CINCO_ESP, SEIS_ESP), (CUATRO_ORO, CINCO_ORO, SEIS_ORO), mano=1)
    # Arranca el mano (j1). Cada baza: cartas del mismo rango → parda.
    estado = jugar_secuencia(
        estado, [CUATRO_ORO, CUATRO_ESP, CINCO_ORO, CINCO_ESP, SEIS_ORO, SEIS_ESP]
    )
    assert estado.terminada
    assert estado.ganador == 1  # el mano
    assert all(b.ganador is None for b in estado.bazas)


def test_parda_primera_arranca_el_mano_la_segunda() -> None:
    # Tras una parda, el que abre la baza siguiente es el mano, no el rival.
    estado = iniciar((CUATRO_ESP, MACHO, SEIS_ESP), (CUATRO_ORO, BASTO, SEIS_ORO), mano=0)
    estado = jugar(estado, CUATRO_ESP)  # j0
    estado = jugar(estado, CUATRO_ORO)  # j1 → parda
    assert estado.turno == 0  # vuelve a arrancar el mano (j0)
