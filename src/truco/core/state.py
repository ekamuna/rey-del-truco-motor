"""Estado de una ronda de truco: completo vs observable.

Referencia: ``docs/REGLAMENTO.md`` §3.

La distinción es la pieza más importante del proyecto para el ML futuro:

* :class:`EstadoRonda` — estado **completo** (las dos manos). Vive en el motor.
* :class:`EstadoObservable` — lo que ve **un** jugador (su mano + la mesa),
  nunca las cartas ocultas del rival. Es lo que recibirá un agente.

Jugadores identificados por índice ``0`` y ``1``.
"""

from __future__ import annotations

from dataclasses import dataclass

from truco.core.cards import Carta


@dataclass(frozen=True, slots=True)
class ResultadoBaza:
    """Una baza ya jugada: la carta de cada jugador y quién la ganó."""

    cartas: tuple[Carta, Carta]  # indexado por jugador (0, 1)
    ganador: int | None  # 0, 1, o None si fue parda


@dataclass(frozen=True, slots=True)
class EstadoRonda:
    """Estado completo e inmutable de una ronda en curso o terminada."""

    manos: tuple[tuple[Carta, ...], tuple[Carta, ...]]  # cartas en mano de j0 y j1
    mano: int  # jugador "mano" de la ronda
    turno: int  # a quién le toca jugar
    mesa: tuple[Carta | None, Carta | None]  # baza parcial, por jugador
    bazas: tuple[ResultadoBaza, ...]  # bazas completas
    ganador: int | None  # ganador de la ronda
    terminada: bool


@dataclass(frozen=True, slots=True)
class EstadoObservable:
    """Lo que un jugador puede ver. NO incluye la mano del rival."""

    jugador: int
    mi_mano: tuple[Carta, ...]
    mano: int  # quién es el "mano" de la ronda
    turno: int
    mesa: tuple[Carta | None, Carta | None]  # cartas ya jugadas en la baza actual
    bazas: tuple[ResultadoBaza, ...]  # bazas completas (públicas)
    cartas_rival: int  # cuántas cartas le quedan al rival
    terminada: bool
    ganador: int | None

    @property
    def soy_mano(self) -> bool:
        return self.jugador == self.mano
