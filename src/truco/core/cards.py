"""Cartas del truco: representación, jerarquía y valor de envido.

Referencia: ``docs/REGLAMENTO.md`` §1 (Cartas y jerarquía).

Dos "fuerzas" conviven en cada carta y NO coinciden:

* :func:`fuerza_truco` — poder para ganar bazas. Mayor gana; igual = *parda*.
* :func:`valor_envido` — puntos para el envido (las figuras valen 0).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Palo(Enum):
    ESPADA = "espada"
    BASTO = "basto"
    ORO = "oro"
    COPA = "copa"


#: Números que existen en la baraja del truco (baraja española sin 8 ni 9).
NUMEROS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)

#: Figuras (sota, caballo, rey): valen 0 para el envido.
FIGURAS: frozenset[int] = frozenset({10, 11, 12})

#: Las 4 "bravas", de la más fuerte a la cuarta, con su poder único (§1).
_PODER_BRAVAS: dict[tuple[int, Palo], int] = {
    (1, Palo.ESPADA): 13,  # el macho
    (1, Palo.BASTO): 12,  # la hembra
    (7, Palo.ESPADA): 11,
    (7, Palo.ORO): 10,
}

#: Poder del resto, por número (todos los palos empatan → parda).
#: Acá el 1 y el 7 son los "falsos" (los bravos ya se resolvieron arriba).
_PODER_POR_NUMERO: dict[int, int] = {
    3: 9,
    2: 8,
    1: 7,  # ases falsos (copa / oro)
    12: 6,  # rey
    11: 5,  # caballo
    10: 4,  # sota
    7: 3,  # sietes falsos (copa / basto)
    6: 2,
    5: 1,
    4: 0,
}


@dataclass(frozen=True, slots=True)
class Carta:
    """Una carta inmutable de la baraja del truco."""

    numero: int
    palo: Palo

    def __post_init__(self) -> None:
        if self.numero not in NUMEROS:
            raise ValueError(f"Número inválido para el truco: {self.numero!r}")

    def __str__(self) -> str:
        return f"{self.numero} de {self.palo.value}"


def fuerza_truco(carta: Carta) -> int:
    """Poder de la carta para ganar bazas.

    Mayor valor gana la baza; **igual valor = parda**. Las 4 bravas tienen
    valores únicos por encima de todo el resto; las demás cartas comparten
    valor con las de su mismo número (por eso empardan). Ver §1.
    """
    brava = _PODER_BRAVAS.get((carta.numero, carta.palo))
    if brava is not None:
        return brava
    return _PODER_POR_NUMERO[carta.numero]


def valor_envido(carta: Carta) -> int:
    """Valor de la carta para el envido: figuras 0, resto su número. Ver §1."""
    return 0 if carta.numero in FIGURAS else carta.numero


def baraja() -> list[Carta]:
    """Las 40 cartas de la baraja española del truco (sin 8 ni 9)."""
    return [Carta(numero, palo) for palo in Palo for numero in NUMEROS]
