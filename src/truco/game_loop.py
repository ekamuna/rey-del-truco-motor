"""Bucle de juego: orquesta agentes y motor hasta terminar la ronda.

Depende de :mod:`truco.agents` y :mod:`truco.core`, nunca de la UI. El mismo
bucle sirve para humano-vs-máquina, máquina-vs-máquina o self-play.
"""

from __future__ import annotations

from collections.abc import Callable

from truco.agents.base import Agent
from truco.core.acciones import Accion
from truco.core.engine import acciones_legales, actor, aplicar, observacion_de
from truco.core.state import EstadoRonda

#: Callback opcional tras cada acción, para que la UI la narre.
#: Recibe ``(estado_antes, quien, accion, estado_despues)``.
AlActuar = Callable[[EstadoRonda, int, Accion, EstadoRonda], None]


def jugar_ronda(
    estado: EstadoRonda,
    agentes: tuple[Agent, Agent],
    al_actuar: AlActuar | None = None,
) -> EstadoRonda:
    """Juega una ronda hasta el final y devuelve el estado terminado."""
    while not estado.terminada:
        quien = actor(estado)
        obs = observacion_de(estado, quien)
        acciones = acciones_legales(estado)
        accion = agentes[quien].actuar(obs, acciones)
        if accion not in acciones:
            raise ValueError(f"El agente {quien} eligió una acción ilegal: {accion}")
        antes = estado
        estado = aplicar(estado, accion)
        if al_actuar is not None:
            al_actuar(antes, quien, accion, estado)

    return estado
