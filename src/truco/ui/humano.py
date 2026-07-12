"""Agente humano: muestra el tablero y un menú de acciones, y lee la elección.

Vive en ``ui`` (no en ``agents``) porque es un adaptador de interfaz. La
entrada/salida se inyectan para poder testearlo sin stdin real.
"""

from __future__ import annotations

from collections.abc import Callable

from truco.agents.base import Agent
from truco.core.acciones import Accion
from truco.core.state import EstadoObservable
from truco.ui.narrador import menu, tablero


class AgenteHumano(Agent):
    """Pide la jugada al humano por consola, con menú de acciones legales."""

    def __init__(
        self,
        leer: Callable[[str], str] = input,
        escribir: Callable[[str], None] = print,
    ) -> None:
        self._leer = leer
        self._escribir = escribir

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        self._escribir(tablero(obs))
        self._escribir(menu(acciones))
        maximo = len(acciones) - 1
        while True:
            crudo = self._leer(f"  → elegí (0-{maximo}): ").strip()
            try:
                indice = int(crudo)
            except ValueError:
                self._escribir("  Entrada inválida: escribí un número.")
                continue
            if 0 <= indice <= maximo:
                return acciones[indice]
            self._escribir(f"  Fuera de rango (0-{maximo}), probá de nuevo.")
