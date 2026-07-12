"""La tabla Q: el "modelo" aprendido. Es legible y se guarda como JSON.

``valor(clave, acción)`` = qué tan buena resultó, en promedio, esa acción en ese
estado. La política es: elegir la acción de mayor valor.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from truco.rl.estado import AccionQ, ClaveEstado


class QTable:
    """Mapa ``(estado abstracto, acción) → valor`` con utilidades de política."""

    def __init__(self) -> None:
        self.q: dict[str, float] = {}

    def valor(self, clave: ClaveEstado, accion: AccionQ) -> float:
        return self.q.get(_k(clave, accion), 0.0)

    def mejor(self, clave: ClaveEstado, legales: list[AccionQ]) -> AccionQ:
        """La acción legal de mayor valor (empates → la primera; 0.0 si nunca vista)."""
        return max(legales, key=lambda a: self.valor(clave, a))

    def epsilon_greedy(
        self, clave: ClaveEstado, legales: list[AccionQ], epsilon: float, rng: random.Random
    ) -> AccionQ:
        """Explora (al azar) con probabilidad ``epsilon``; si no, explota la mejor."""
        if rng.random() < epsilon:
            return rng.choice(legales)
        return self.mejor(clave, legales)

    def actualizar(self, clave: ClaveEstado, accion: AccionQ, objetivo: float, alfa: float) -> None:
        """Acerca el valor hacia ``objetivo`` un paso ``alfa`` (aprendizaje)."""
        actual = self.valor(clave, accion)
        self.q[_k(clave, accion)] = actual + alfa * (objetivo - actual)

    def __len__(self) -> int:
        return len(self.q)

    # --- Persistencia (el archivo-modelo) ------------------------------------

    def guardar(self, ruta: Path) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(self.q, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def cargar(cls, ruta: Path) -> QTable:
        tabla = cls()
        tabla.q = {k: float(v) for k, v in json.loads(ruta.read_text(encoding="utf-8")).items()}
        return tabla


def _k(clave: ClaveEstado, accion: AccionQ) -> str:
    return f"{clave}|{accion.value}"
