"""Agente humano: renderiza el estado y lee la elección por terminal.

Vive en ``ui`` (no en ``agents``) porque es un adaptador de interfaz. La
entrada/salida se inyectan para poder testearlo sin stdin real.
"""

from __future__ import annotations

from collections.abc import Callable

from truco.agents.base import Accion, Agent
from truco.core.state import EstadoObservable
from truco.ui.render import formato_observacion


class AgenteHumano(Agent):
    """Pide la jugada al humano por consola."""

    def __init__(
        self,
        leer: Callable[[str], str] = input,
        escribir: Callable[[str], None] = print,
    ) -> None:
        self._leer = leer
        self._escribir = escribir

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        self._escribir(formato_observacion(obs))
        maximo = len(acciones) - 1
        while True:
            crudo = self._leer(f"Elegí carta (0-{maximo}): ").strip()
            try:
                indice = int(crudo)
            except ValueError:
                self._escribir("Entrada inválida: escribí un número.")
                continue
            if 0 <= indice <= maximo:
                return acciones[indice]
            self._escribir(f"Fuera de rango (0-{maximo}), probá de nuevo.")
