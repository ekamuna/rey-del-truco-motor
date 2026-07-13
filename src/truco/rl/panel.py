"""Examen del panel: cada contendiente contra rivales de distinto estilo.

Comando: ``uv run truco-panel``. Mide winrate de partidas de cada agente contra
un panel (azar, reglas, agresivo, mentiroso, conservador) y muestra una tabla.
"""

from __future__ import annotations

from pathlib import Path

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.estilos import agresivo, conservador, mentiroso
from truco.agents.reglas import AgenteReglas
from truco.evaluacion import FabricaAgente, enfrentar
from truco.rl.agente_q import AgenteQ
from truco.rl.agente_red import AgenteRed
from truco.rl.qtable import QTable

_RUTA_Q = Path("modelos/qtable.json")
_RUTA_RED = Path("modelos/red.pt")


def _panel() -> dict[str, FabricaAgente]:
    return {
        "Aleatorio": lambda: AgenteAleatorio(seed=7),
        "Reglas": lambda: AgenteReglas(),
        "Agresivo": lambda: agresivo(7),
        "Mentiroso": lambda: mentiroso(7),
        "Conservad": lambda: conservador(7),
    }


def _contendientes() -> dict[str, FabricaAgente]:
    ags: dict[str, FabricaAgente] = {"Bot reglas": lambda: AgenteReglas()}
    if _RUTA_Q.exists():
        q = QTable.cargar(_RUTA_Q)
        ags["Q tabular"] = lambda: AgenteQ(q)
    if _RUTA_RED.exists():
        red = AgenteRed.cargar(_RUTA_RED).red
        ags["Red (deep RL)"] = lambda: AgenteRed(red)
    return ags


def evaluar_panel(partidas: int = 400, seed: int = 99) -> None:
    panel = _panel()
    cols = list(panel)
    print(f"Winrate en {partidas} partidas (fila = contendiente, columna = rival)\n")
    print("Contendiente".ljust(15) + "".join(c.rjust(11) for c in cols) + "   PROM")
    print("-" * (15 + 11 * len(cols) + 7))
    for nombre, fabrica in _contendientes().items():
        tasas = [
            enfrentar(fabrica, panel[col], partidas=partidas, seed=seed).winrate_a for col in cols
        ]
        promedio = sum(tasas) / len(tasas)
        print(nombre.ljust(15) + "".join(f"{t:10.0%} " for t in tasas) + f"  {promedio:5.0%}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Panel de estilos: ¿quién le gana a quién?")
    parser.add_argument("--partidas", type=int, default=400)
    args = parser.parse_args()
    evaluar_panel(partidas=args.partidas)
