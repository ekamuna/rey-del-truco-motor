"""Partida completa: se juegan rondas hasta que alguien llega al objetivo.

Referencia: ``docs/REGLAMENTO.md`` §8 (puntaje y formato de partida).

El rol de "mano" alterna cada ronda. La falta envido usa el marcador actual.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from truco.agents.base import Agent
from truco.core.engine import nueva_ronda
from truco.game_loop import jugar_ronda


@dataclass(frozen=True, slots=True)
class ResultadoPartida:
    puntos: tuple[int, int]
    ganador: int
    rondas: int


def jugar_partida(
    agentes: tuple[Agent, Agent],
    objetivo: int = 15,
    seed: int | None = None,
    mano_inicial: int = 0,
    max_rondas: int = 1000,
) -> ResultadoPartida:
    """Juega una partida completa a ``objetivo`` puntos y devuelve el resultado."""
    rng = random.Random(seed)
    puntos = (0, 0)
    mano = mano_inicial
    rondas = 0

    while max(puntos) < objetivo and rondas < max_rondas:
        estado = nueva_ronda(
            seed=rng.randrange(2**31),
            mano=mano,
            puntos_partida=puntos,
            objetivo=objetivo,
        )
        estado = jugar_ronda(estado, agentes)
        puntos = (
            puntos[0] + estado.puntos_ronda[0],
            puntos[1] + estado.puntos_ronda[1],
        )
        mano = 1 - mano
        rondas += 1

    ganador = 0 if puntos[0] > puntos[1] else 1
    return ResultadoPartida(puntos=puntos, ganador=ganador, rondas=rondas)
