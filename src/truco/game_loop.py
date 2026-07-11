"""Bucle de juego: orquesta agentes y motor hasta terminar la ronda.

Depende de :mod:`truco.agents` y :mod:`truco.core`, nunca de la UI. El mismo
bucle sirve para humano-vs-máquina, máquina-vs-máquina o self-play.
"""

from __future__ import annotations

from collections.abc import Callable

from truco.agents.base import Agent
from truco.core.cards import Carta
from truco.core.engine import acciones_legales, jugar, observacion_de
from truco.core.state import EstadoRonda

#: Callback opcional que se invoca tras cada jugada (para que la UI la muestre).
AlJugar = Callable[[EstadoRonda, int, Carta], None]


def jugar_ronda(
    estado: EstadoRonda,
    agentes: tuple[Agent, Agent],
    al_jugar: AlJugar | None = None,
) -> EstadoRonda:
    """Juega una ronda hasta el final y devuelve el estado terminado.

    En cada turno le pide al agente de turno una acción, validando que sea
    legal (un agente que devuelve una carta ilegal es un error de programación).
    """
    while not estado.terminada:
        jugador = estado.turno
        obs = observacion_de(estado, jugador)
        acciones = acciones_legales(estado)
        carta = agentes[jugador].actuar(obs, acciones)
        if carta not in acciones:
            raise ValueError(f"El agente {jugador} eligió una acción ilegal: {carta}")
        estado = jugar(estado, carta)
        if al_jugar is not None:
            al_jugar(estado, jugador, carta)

    return estado
