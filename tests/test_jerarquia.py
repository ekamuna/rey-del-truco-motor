"""Tests de la jerarquía de cartas y el valor de envido (REGLAMENTO §1).

El corazón del motor: si esto está bien, el resto se apoya sobre una base firme.
Cubre explícitamente las dos trampas clásicas (el 1 y el 7 "falsos").
"""

import pytest

from truco.core.cards import Carta, Palo, baraja, fuerza_truco, valor_envido

# Orden de poder de mayor a menor, un representante por nivel (§1).
ORDEN_ESPERADO: list[Carta] = [
    Carta(1, Palo.ESPADA),  # 1
    Carta(1, Palo.BASTO),  # 2
    Carta(7, Palo.ESPADA),  # 3
    Carta(7, Palo.ORO),  # 4
    Carta(3, Palo.ORO),  # 5  · los 3
    Carta(2, Palo.COPA),  # 6  · los 2
    Carta(1, Palo.ORO),  # 7  · as falso
    Carta(12, Palo.BASTO),  # 8  · rey
    Carta(11, Palo.ESPADA),  # 9  · caballo
    Carta(10, Palo.COPA),  # 10 · sota
    Carta(7, Palo.COPA),  # 11 · siete falso
    Carta(6, Palo.ORO),  # 12
    Carta(5, Palo.BASTO),  # 13
    Carta(4, Palo.ESPADA),  # 14
]

BRAVAS: list[Carta] = [
    Carta(1, Palo.ESPADA),
    Carta(1, Palo.BASTO),
    Carta(7, Palo.ESPADA),
    Carta(7, Palo.ORO),
]


def test_orden_estricto_decreciente() -> None:
    fuerzas = [fuerza_truco(c) for c in ORDEN_ESPERADO]
    assert fuerzas == sorted(fuerzas, reverse=True)
    assert len(set(fuerzas)) == len(fuerzas), "cada nivel debe ser único"


def test_bravas_son_las_cuatro_mas_fuertes() -> None:
    fuerza_min_brava = min(fuerza_truco(c) for c in BRAVAS)
    resto = [c for c in baraja() if c not in BRAVAS]
    assert fuerza_min_brava > max(fuerza_truco(c) for c in resto)


def test_uno_falso_es_bajo() -> None:
    # El 1 de oro/copa NO es alto: está debajo del 2 y apenas arriba del rey.
    assert fuerza_truco(Carta(1, Palo.ORO)) < fuerza_truco(Carta(2, Palo.ESPADA))
    assert fuerza_truco(Carta(1, Palo.ORO)) > fuerza_truco(Carta(12, Palo.ESPADA))


def test_siete_falso_es_debil() -> None:
    # El 7 de copa/basto está por debajo de la sota (10).
    assert fuerza_truco(Carta(7, Palo.COPA)) < fuerza_truco(Carta(10, Palo.ESPADA))
    assert fuerza_truco(Carta(7, Palo.BASTO)) < fuerza_truco(Carta(10, Palo.ORO))


def test_parda_mismo_numero_no_bravo() -> None:
    # Dos treses de distinto palo empardan; los sietes falsos entre sí también.
    assert fuerza_truco(Carta(3, Palo.ORO)) == fuerza_truco(Carta(3, Palo.COPA))
    assert fuerza_truco(Carta(7, Palo.COPA)) == fuerza_truco(Carta(7, Palo.BASTO))


def test_bravas_no_empardan() -> None:
    assert fuerza_truco(Carta(1, Palo.ESPADA)) != fuerza_truco(Carta(1, Palo.BASTO))
    assert fuerza_truco(Carta(7, Palo.ESPADA)) != fuerza_truco(Carta(7, Palo.ORO))


def test_una_brava_nunca_pardea_con_no_brava() -> None:
    for brava in BRAVAS:
        for otra in baraja():
            if otra not in BRAVAS:
                assert fuerza_truco(brava) != fuerza_truco(otra)


def test_valor_envido_figuras_cero() -> None:
    for numero in (10, 11, 12):
        assert valor_envido(Carta(numero, Palo.ESPADA)) == 0


def test_valor_envido_numericas() -> None:
    assert valor_envido(Carta(7, Palo.ORO)) == 7
    assert valor_envido(Carta(1, Palo.BASTO)) == 1
    assert valor_envido(Carta(6, Palo.COPA)) == 6


def test_envido_maximo_es_33() -> None:
    # 6 y 7 del mismo palo: 6 + 7 + 20 = 33.
    assert valor_envido(Carta(6, Palo.ORO)) + valor_envido(Carta(7, Palo.ORO)) + 20 == 33


def test_baraja_completa_y_sin_duplicados() -> None:
    b = baraja()
    assert len(b) == 40
    assert len(set(b)) == 40
    assert all(c.numero not in (8, 9) for c in b)


def test_numero_invalido_lanza_error() -> None:
    with pytest.raises(ValueError):
        Carta(8, Palo.ESPADA)
