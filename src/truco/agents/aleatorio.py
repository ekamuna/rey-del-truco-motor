"""Agente aleatorio — la línea base más tonta (elige una acción al azar).

Sirve como rival trivial y como referencia: cualquier bot que valga la pena
debe ganarle holgadamente. El azar es reproducible por ``seed``.
"""

from __future__ import annotations

import random

from truco.agents.base import Agent
from truco.core.acciones import Accion
from truco.core.state import EstadoObservable


class AgenteAleatorio(Agent):
    """Elige uniformemente entre las acciones legales (incluye cantos y mazo)."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        return self._rng.choice(acciones)
