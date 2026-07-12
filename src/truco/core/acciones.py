"""Acciones que un jugador puede tomar en una ronda.

Referencia: ``docs/REGLAMENTO.md`` §4, §5, §6, §7.

Una :class:`Accion` es jugar una carta, cantar (envido/truco y variantes),
responder (quiero / no quiero) o irse al mazo. Se usa como espacio de acciones
unificado para el motor y los agentes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from truco.core.cards import Carta


class TipoAccion(Enum):
    JUGAR = "jugar"
    # Envido y variantes
    ENVIDO = "envido"
    REAL_ENVIDO = "real envido"
    FALTA_ENVIDO = "falta envido"
    # Truco y variantes
    TRUCO = "truco"
    RETRUCO = "retruco"
    VALE_CUATRO = "vale cuatro"
    # Respuestas
    QUIERO = "quiero"
    NO_QUIERO = "no quiero"
    # Abandono
    MAZO = "mazo"


#: Cantos de la familia del envido (en orden de escalada).
CANTOS_ENVIDO = (TipoAccion.ENVIDO, TipoAccion.REAL_ENVIDO, TipoAccion.FALTA_ENVIDO)
#: Cantos de la familia del truco (en orden de escalada).
CANTOS_TRUCO = (TipoAccion.TRUCO, TipoAccion.RETRUCO, TipoAccion.VALE_CUATRO)

CATEGORIA_ENVIDO = "envido"
CATEGORIA_TRUCO = "truco"


def categoria_de(tipo: TipoAccion) -> str:
    """Categoría de negociación de un canto: ``envido`` o ``truco``."""
    if tipo in CANTOS_ENVIDO:
        return CATEGORIA_ENVIDO
    if tipo in CANTOS_TRUCO:
        return CATEGORIA_TRUCO
    raise ValueError(f"{tipo} no es un canto")


@dataclass(frozen=True, slots=True)
class Accion:
    """Una acción concreta. ``carta`` solo se usa (y es obligatoria) para JUGAR."""

    tipo: TipoAccion
    carta: Carta | None = None

    def __post_init__(self) -> None:
        es_jugar = self.tipo is TipoAccion.JUGAR
        if es_jugar and self.carta is None:
            raise ValueError("JUGAR requiere una carta.")
        if not es_jugar and self.carta is not None:
            raise ValueError(f"{self.tipo} no lleva carta.")

    def __str__(self) -> str:
        if self.tipo is TipoAccion.JUGAR:
            return f"jugar {self.carta}"
        return str(self.tipo.value)


def jugar_carta(carta: Carta) -> Accion:
    """Atajo para construir una acción de jugar una carta."""
    return Accion(TipoAccion.JUGAR, carta)


def canto(tipo: TipoAccion) -> Accion:
    """Atajo para construir una acción de canto/respuesta (sin carta)."""
    return Accion(tipo)
