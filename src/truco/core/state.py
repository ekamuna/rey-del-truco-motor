"""Estado de una ronda de truco: completo vs observable.

Referencia: ``docs/REGLAMENTO.md`` §3-§8.

* :class:`EstadoRonda` — estado **completo** (las dos manos + toda la
  negociación). Vive en el motor.
* :class:`EstadoObservable` — lo que ve **un** jugador. Incluye lo público de la
  negociación (los cantos son a viva voz) pero nunca las cartas del rival.

Jugadores identificados por índice ``0`` y ``1``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from truco.core.acciones import TipoAccion
from truco.core.cards import Carta


@dataclass(frozen=True, slots=True)
class ResultadoBaza:
    """Una baza ya jugada: la carta de cada jugador y quién la ganó."""

    cartas: tuple[Carta, Carta]  # indexado por jugador (0, 1)
    ganador: int | None  # 0, 1, o None si fue parda


@dataclass(frozen=True, slots=True)
class Negociacion:
    """Un canto en curso esperando respuesta (quiero / no quiero / subir)."""

    categoria: str  # CATEGORIA_ENVIDO o CATEGORIA_TRUCO
    cantos: tuple[TipoAccion, ...]  # cadena de cantos hechos, ej: (ENVIDO, REAL_ENVIDO)
    a_responder: int  # jugador que debe responder

    @property
    def ultimo(self) -> TipoAccion:
        return self.cantos[-1]

    @property
    def cantor(self) -> int:
        """Quién hizo el último canto (el que espera respuesta)."""
        return 1 - self.a_responder


@dataclass(frozen=True, slots=True)
class EstadoRonda:
    """Estado completo e inmutable de una ronda."""

    # --- Contexto de la partida (para falta envido y cierre) ---
    puntos_partida: tuple[int, int]
    objetivo: int

    # --- Cartas y bazas ---
    manos: tuple[tuple[Carta, ...], tuple[Carta, ...]]
    mano: int  # jugador "mano" de la ronda
    turno: int  # de quién es el turno (fuera de negociación)
    mesa: tuple[Carta | None, Carta | None]  # baza parcial, por jugador
    bazas: tuple[ResultadoBaza, ...]

    # --- Negociación ---
    pendiente: Negociacion | None = None
    truco_suspendido: Negociacion | None = None  # truco interrumpido por "envido primero"

    # --- Envido ---
    tantos: tuple[int, int] = (0, 0)  # tanto de cada jugador (fijado al repartir)
    envido_resuelto: bool = False
    envido_ganador: int | None = None
    puntos_envido: int = 0

    # --- Truco ---
    nivel_truco: int = 0  # 0 sin cantar, 1 truco, 2 retruco, 3 vale cuatro
    truco_querido: bool = False
    puede_subir_truco: int | None = None  # quién puede subir el truco

    # --- Puntos y cierre ---
    puntos_ronda: tuple[int, int] = (0, 0)
    terminada: bool = False
    ganador: int | None = None  # ganador del truco/bazas (informativo)
    motivo: str = ""  # "bazas" | "no_quiero_truco" | "mazo"


@dataclass(frozen=True, slots=True)
class EstadoObservable:
    """Lo que un jugador puede ver. NO incluye la mano del rival."""

    jugador: int
    mi_mano: tuple[Carta, ...]
    mano: int
    turno: int
    mesa: tuple[Carta | None, Carta | None]
    bazas: tuple[ResultadoBaza, ...]
    cartas_rival: int

    pendiente: Negociacion | None
    nivel_truco: int
    truco_querido: bool
    envido_resuelto: bool

    puntos_partida: tuple[int, int]
    objetivo: int

    terminada: bool
    ganador: int | None
    puntos_ronda: tuple[int, int]

    # Campos con default al final (por orden de dataclass).
    mi_tanto: int = field(default=0)

    @property
    def soy_mano(self) -> bool:
        return self.jugador == self.mano
