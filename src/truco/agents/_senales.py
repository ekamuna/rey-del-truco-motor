"""Lectura de señales del rival desde el :class:`EstadoObservable` (funciones puras).

Base común de los **rivales realistas** del panel (mentiroso que calcula, estratega
que induce). Toda la info sale del observable sin tocar el motor: qué jugó el rival,
si pasó el envido, si tiró carta baja, el marcador. Referencia: ``docs/NORTE.md`` T4.
"""

from __future__ import annotations

from truco.core.cards import fuerza_truco, valor_envido
from truco.core.state import EstadoObservable

BRAVA = 10  # fuerza_truco >= 10 es una brava (las 4 altas)
CARTA_BAJA_FUERZA = 3  # <= 3: 7-falso, 6, 5, 4 → el rival "tira basura"


def n_bravas(obs: EstadoObservable) -> int:
    return sum(fuerza_truco(c) >= BRAVA for c in obs.mi_mano)


def fuerza_max(obs: EstadoObservable) -> int:
    return max((fuerza_truco(c) for c in obs.mi_mano), default=0)


def es_premium(obs: EstadoObservable) -> bool:
    """Mano top (~8%): dos bravas, o una brava con buen tanto."""
    b = n_bravas(obs)
    return b >= 2 or (b >= 1 and obs.mi_tanto >= 29)


def rival_lidero_baza(obs: EstadoObservable) -> bool:
    """El rival ya jugó su carta en la baza en curso y yo todavía no."""
    return obs.mesa[1 - obs.jugador] is not None and obs.mesa[obs.jugador] is None


def rival_paso_envido(obs: EstadoObservable) -> bool:
    """SEÑAL FUERTE: el rival lideró la 1ª baza sin cantar envido teniendo el derecho
    → prior de tanto bajo (sólo el ~25% pasa de 27)."""
    return len(obs.bazas) == 0 and rival_lidero_baza(obs) and not obs.envido_resuelto


def rival_tiro_baja(obs: EstadoObservable) -> bool:
    c = obs.mesa[1 - obs.jugador]
    return c is not None and fuerza_truco(c) <= CARTA_BAJA_FUERZA


def gane_baza1(obs: EstadoObservable) -> bool:
    return bool(obs.bazas) and obs.bazas[0].ganador == obs.jugador


def perdi_baza1(obs: EstadoObservable) -> bool:
    return bool(obs.bazas) and obs.bazas[0].ganador == (1 - obs.jugador)


def rival_va_ganando(obs: EstadoObservable, umbral: int = 3) -> bool:
    rival = 1 - obs.jugador
    return obs.puntos_partida[rival] - obs.puntos_partida[obs.jugador] >= umbral


def debilidad_rival(obs: EstadoObservable) -> float:
    """Debilidad estimada del rival (0..1) por señales intra-ronda: pasó el envido,
    tiró carta baja liderando, o mostró cartas de bajo valor de envido."""
    s = 0.0
    if rival_paso_envido(obs):
        s += 0.5
    if rival_tiro_baja(obs):
        s += 0.3
    c = obs.mesa[1 - obs.jugador]
    if c is not None and valor_envido(c) <= 4:
        s += 0.2
    return min(1.0, s)
