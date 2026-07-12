"""Entrenamiento por refuerzo (Monte Carlo control) contra un rival.

El agente que aprende es el jugador 0. Juega rondas contra un rival; al terminar
cada una mira el resultado (puntos ganados - perdidos) y **acerca** el valor de
cada jugada que hizo hacia ese resultado. Las jugadas que llevan a ganar suben
de valor; las que llevan a perder bajan. Nadie escribe la estrategia.

Se entrena contra un rival fijo (más estable que el self-play ingenuo). Se puede
continuar el entrenamiento de una tabla contra otro rival (currículum).
"""

from __future__ import annotations

import random

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.base import Agent
from truco.core.engine import acciones_legales, actor, aplicar, nueva_ronda, observacion_de
from truco.core.state import EstadoRonda
from truco.evaluacion import FabricaAgente, enfrentar
from truco.rl.agente_q import AgenteQ
from truco.rl.estado import AccionQ, ClaveEstado, a_concreta, acciones_legales_q, clave_estado
from truco.rl.qtable import QTable

Trayectoria = list[tuple[ClaveEstado, AccionQ]]
_APRENDIZ = 0  # el jugador que aprende


def _episodio(
    estado: EstadoRonda, tabla: QTable, rival: Agent, epsilon: float, rng: random.Random
) -> tuple[EstadoRonda, Trayectoria]:
    """Juega una ronda (aprendiz vs rival) y registra las (clave, acción) del aprendiz."""
    traje: Trayectoria = []
    while not estado.terminada:
        jugador = actor(estado)
        obs = observacion_de(estado, jugador)
        concretas = acciones_legales(estado)
        if jugador == _APRENDIZ:
            clave = clave_estado(obs)
            accion_q = tabla.epsilon_greedy(clave, acciones_legales_q(obs, concretas), epsilon, rng)
            traje.append((clave, accion_q))
            accion = a_concreta(accion_q, obs, concretas)
        else:
            accion = rival.actuar(obs, concretas)
        estado = aplicar(estado, accion)
    return estado, traje


def entrenar(
    episodios: int = 60_000,
    rival: Agent | None = None,
    tabla: QTable | None = None,
    alfa: float = 0.1,
    epsilon_inicial: float = 0.30,
    epsilon_final: float = 0.02,
    seed: int = 0,
    eval_cada: int = 0,
    eval_partidas: int = 300,
) -> tuple[QTable, list[tuple[int, float]]]:
    """Entrena una tabla Q contra ``rival``. Devuelve (tabla, curva de winrate vs Aleatorio)."""
    tabla = tabla or QTable()
    rival = rival or AgenteAleatorio(seed=seed + 1)
    rng = random.Random(seed)
    curva: list[tuple[int, float]] = []

    for ep in range(episodios):
        epsilon = epsilon_inicial + (epsilon_final - epsilon_inicial) * (ep / episodios)
        estado = nueva_ronda(seed=rng.randrange(2**31), mano=ep % 2)
        final, traje = _episodio(estado, tabla, rival, epsilon, rng)

        diff = final.puntos_ronda[_APRENDIZ] - final.puntos_ronda[1 - _APRENDIZ]
        recompensa = float((diff > 0) - (diff < 0))  # +1 gané la ronda, -1 perdí, 0 empate
        for clave, accion_q in traje:
            tabla.actualizar(clave, accion_q, recompensa, alfa)

        if eval_cada and ep % eval_cada == 0:
            curva.append((ep, winrate_vs(tabla, lambda: AgenteAleatorio(seed=1), eval_partidas)))

    return tabla, curva


def winrate_vs(tabla: QTable, rival_factory: FabricaAgente, partidas: int = 500) -> float:
    """Winrate de partidas del AgenteQ (greedy) contra un rival, con semilla fija."""
    return enfrentar(lambda: AgenteQ(tabla), rival_factory, partidas=partidas, seed=12345).winrate_a


def main() -> None:
    """Comando de consola: entrena por refuerzo y guarda el modelo (la tabla Q)."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Entrenar el agente Q de truco por refuerzo.")
    parser.add_argument("--episodios", type=int, default=80_000, help="rondas de entrenamiento")
    parser.add_argument("--salida", default="modelos/qtable.json", help="dónde guardar el modelo")
    args = parser.parse_args()

    print(f"Entrenando {args.episodios} rondas vs Aleatorio (mirá subir la curva)…\n")
    tabla, curva = entrenar(
        episodios=args.episodios,
        rival=AgenteAleatorio(seed=1),
        eval_cada=max(1, args.episodios // 8),
        eval_partidas=300,
        seed=0,
    )
    for ep, wr in curva:
        print(f"  ronda {ep:>7}:  {wr:5.0%}  " + "█" * int(wr * 40))

    ruta = Path(args.salida)
    tabla.guardar(ruta)
    final = winrate_vs(tabla, lambda: AgenteAleatorio(seed=1), 500)
    print(f"\nModelo guardado en {ruta}  ({len(tabla)} entradas).")
    print(f"Winrate final vs Aleatorio: {final:.0%}")
