"""AgenteQ — juega usando una tabla Q ya entrenada (política greedy).

Implementa la interfaz :class:`Agent`, así se enchufa al mismo bucle, partida y
evaluación que cualquier otro agente. Sin exploración: siempre la mejor jugada.
"""

from __future__ import annotations

from truco.agents.base import Agent
from truco.core.acciones import Accion
from truco.core.state import EstadoObservable
from truco.rl.estado import a_concreta, acciones_legales_q, clave_estado
from truco.rl.qtable import QTable


class AgenteQ(Agent):
    def __init__(self, tabla: QTable) -> None:
        self.tabla = tabla

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        clave = clave_estado(obs)
        legales = acciones_legales_q(obs, acciones)
        mejor = self.tabla.mejor(clave, legales)
        return a_concreta(mejor, obs, acciones)
