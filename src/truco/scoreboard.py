"""Scoreboard: mide un bot contra el panel completo — winrate **y** diferencia de
puntos — con seed fijo, para validar cada mejora de forma reproducible.

Referencia: ``docs/NORTE.md`` (protocolo de validación). Es la vara con la que se
acepta o revierte cada táctica: una mejora vale si **sube el promedio sin romper
ninguna columna**.

Comando: ``uv run truco-scoreboard``.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.base import Agent
from truco.agents.estilos import agresivo, conservador, mentiroso
from truco.agents.pimc import AgentePIMC
from truco.agents.reglas import AgenteReglas
from truco.partida import jugar_partida

FabricaAgente = Callable[[], Agent]


def panel() -> dict[str, FabricaAgente]:
    """El panel de rivales contra el que se mide todo. Se le suman los realistas."""
    return {
        "azar": lambda: AgenteAleatorio(seed=7),
        "reglas": lambda: AgenteReglas(),
        "conservador": lambda: conservador(7),
        "agresivo": lambda: agresivo(7),
        "mentiroso": lambda: mentiroso(7),
    }


@dataclass(frozen=True, slots=True)
class Resultado:
    winrate: float
    dif_media: float


def medir(bot: FabricaAgente, rival: FabricaAgente, partidas: int, seed: int) -> Resultado:
    """Enfrenta ``bot`` (jugador 0) contra ``rival``, alternando la mano inicial."""
    rng = random.Random(seed)
    wins = 0
    dif = 0
    for i in range(partidas):
        r = jugar_partida((bot(), rival()), seed=rng.randrange(2**31), mano_inicial=i % 2)
        wins += int(r.ganador == 0)
        dif += r.puntos[0] - r.puntos[1]
    return Resultado(wins / partidas, dif / partidas)


def scoreboard(bot: FabricaAgente, partidas: int = 300, seed: int = 11) -> dict[str, Resultado]:
    return {nombre: medir(bot, rival, partidas, seed) for nombre, rival in panel().items()}


def promedio(resultados: dict[str, Resultado]) -> float:
    return sum(r.winrate for r in resultados.values()) / len(resultados)


def imprimir(resultados: dict[str, Resultado]) -> None:
    print(f"{'rival':14}{'winrate':>10}{'dif/part':>10}")
    print("-" * 34)
    for nombre, r in resultados.items():
        print(f"{nombre:14}{r.winrate:>9.1%}{r.dif_media:>+10.2f}")
    print("-" * 34)
    print(f"{'PROMEDIO':14}{promedio(resultados):>9.1%}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Scoreboard del bot vs el panel")
    parser.add_argument("--partidas", type=int, default=300)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()
    imprimir(scoreboard(lambda: AgentePIMC(), partidas=args.partidas, seed=args.seed))
