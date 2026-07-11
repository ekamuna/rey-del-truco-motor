"""La interfaz de Agente — el contrato que cumple todo jugador.

Referencia: ``docs/DOCUMENTO-MAESTRO.md`` §4 (la interfaz del Agente).

Un agente recibe **lo que puede ver** (:class:`EstadoObservable`) y la lista de
**acciones legales**, y devuelve la acción elegida. Con esta única firma, pasar
de un bot de reglas a uno de ML es cambiar la implementación, no el bucle.

En la v1 la única acción es *qué carta jugar*; cuando entren los cantos (M4) el
tipo :data:`Accion` se ampliará sin tocar la firma.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from truco.core.cards import Carta
from truco.core.state import EstadoObservable

#: Acción que un agente puede tomar. Hoy es solo una carta; se ampliará con los cantos.
Accion = Carta


class Agent(ABC):
    """Contrato de un jugador de truco."""

    @abstractmethod
    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        """Elige una acción entre las ``acciones`` legales, dado lo observable."""
        ...

    def observar_resultado(self, recompensa: float) -> None:
        """Notifica el resultado de la ronda (recompensa).

        Sólo lo usa el agente de aprendizaje por refuerzo (M6); los demás lo
        ignoran. Con ``+1`` ganó, ``-1`` perdió.
        """
        return None
