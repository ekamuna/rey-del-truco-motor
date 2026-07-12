"""Harness de evaluación: enfrenta dos agentes en muchas partidas y mide winrate.

Referencia: ``docs/ROADMAP.md`` M4 (línea base medible).

Para que la comparación sea justa, se alterna quién es mano inicial en cada
partida (la mano tiene ventaja estructural).
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from truco.agents.base import Agent
from truco.partida import jugar_partida

#: Fábrica de agente: crea un agente nuevo por partida (para no compartir estado/RNG).
FabricaAgente = Callable[[], Agent]


@dataclass(frozen=True, slots=True)
class ResultadoEvaluacion:
    partidas: int
    victorias_a: int
    victorias_b: int

    @property
    def winrate_a(self) -> float:
        return self.victorias_a / self.partidas if self.partidas else 0.0


def enfrentar(
    fabrica_a: FabricaAgente,
    fabrica_b: FabricaAgente,
    partidas: int = 20,
    objetivo: int = 15,
    seed: int | None = None,
) -> ResultadoEvaluacion:
    """Juega ``partidas`` entre A y B, alternando quién arranca de mano."""
    rng = random.Random(seed)
    victorias_a = 0
    for i in range(partidas):
        agentes = (fabrica_a(), fabrica_b())
        resultado = jugar_partida(
            agentes,
            objetivo=objetivo,
            seed=rng.randrange(2**31),
            mano_inicial=i % 2,  # alterna la ventaja de mano
        )
        if resultado.ganador == 0:
            victorias_a += 1
    return ResultadoEvaluacion(
        partidas=partidas,
        victorias_a=victorias_a,
        victorias_b=partidas - victorias_a,
    )
