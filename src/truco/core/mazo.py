"""Reparto de cartas — barajado reproducible por semilla.

Referencia: ``docs/REGLAMENTO.md`` §2 (Reparto e inicio).

El azar usa una ``seed`` para poder **repetir** una partida al depurar o al
entrenar la IA (azar de verdad para el jugador, reproducible para nosotros).
"""

from __future__ import annotations

import random

from truco.core.cards import Carta, baraja

#: Cartas que recibe cada jugador en el reparto de una ronda 1v1.
CARTAS_POR_JUGADOR = 3


def repartir(seed: int | None = None) -> tuple[tuple[Carta, ...], tuple[Carta, ...]]:
    """Baraja las 40 cartas y reparte 3 a cada jugador.

    Devuelve ``(mano_jugador_0, mano_jugador_1)``. Con la misma ``seed`` el
    reparto es idéntico; con ``seed=None`` es aleatorio de verdad.
    """
    cartas = baraja()
    random.Random(seed).shuffle(cartas)
    corte = CARTAS_POR_JUGADOR
    return tuple(cartas[:corte]), tuple(cartas[corte : corte * 2])
