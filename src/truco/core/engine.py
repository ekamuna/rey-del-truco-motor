"""Motor de la ronda: repartir, jugar bazas y resolver quién gana.

Referencia: ``docs/REGLAMENTO.md`` §3 (Estructura de una ronda).

Funciones puras sobre :class:`EstadoRonda`: ``jugar`` no muta, devuelve un
estado nuevo. La resolución de la ronda (con toda la tabla de pardas) vive en
:func:`_resolver_ronda`, aislada para poder cambiarla si hiciera falta.
"""

from __future__ import annotations

from dataclasses import replace

from truco.core.cards import Carta, fuerza_truco
from truco.core.mazo import repartir
from truco.core.state import EstadoObservable, EstadoRonda, ResultadoBaza


def iniciar(
    mano0: tuple[Carta, ...],
    mano1: tuple[Carta, ...],
    mano: int = 0,
) -> EstadoRonda:
    """Crea una ronda a partir de dos manos ya repartidas.

    ``mano`` es el jugador que arranca (juega primero la baza 1 y gana los
    empates de la ronda). Útil para tests deterministas.
    """
    return EstadoRonda(
        manos=(tuple(mano0), tuple(mano1)),
        mano=mano,
        turno=mano,
        mesa=(None, None),
        bazas=(),
        ganador=None,
        terminada=False,
    )


def nueva_ronda(seed: int | None = None, mano: int = 0) -> EstadoRonda:
    """Reparte (reproducible por ``seed``) e inicia una ronda."""
    mano0, mano1 = repartir(seed)
    return iniciar(mano0, mano1, mano=mano)


def acciones_legales(estado: EstadoRonda) -> tuple[Carta, ...]:
    """Cartas que el jugador de turno puede jugar (vacío si la ronda terminó)."""
    if estado.terminada:
        return ()
    return estado.manos[estado.turno]


def observacion_de(estado: EstadoRonda, jugador: int) -> EstadoObservable:
    """Proyecta el estado completo a lo que ``jugador`` puede ver."""
    rival = 1 - jugador
    return EstadoObservable(
        jugador=jugador,
        mi_mano=estado.manos[jugador],
        mano=estado.mano,
        turno=estado.turno,
        mesa=estado.mesa,
        bazas=estado.bazas,
        cartas_rival=len(estado.manos[rival]),
        terminada=estado.terminada,
        ganador=estado.ganador,
    )


def jugar(estado: EstadoRonda, carta: Carta) -> EstadoRonda:
    """Juega ``carta`` por el jugador de turno y devuelve el nuevo estado.

    Levanta error si la ronda terminó o si la carta no está en la mano del
    jugador de turno.
    """
    if estado.terminada:
        raise RuntimeError("La ronda ya terminó; no se pueden jugar cartas.")

    j = estado.turno
    if carta not in estado.manos[j]:
        raise ValueError(f"El jugador {j} no tiene la carta {carta}.")

    # Sacar la carta de la mano y ponerla en la mesa.
    manos = list(estado.manos)
    manos[j] = tuple(c for c in manos[j] if c != carta)
    mesa: list[Carta | None] = list(estado.mesa)
    mesa[j] = carta

    rival = 1 - j
    if mesa[rival] is None:
        # Falta que el rival juegue su carta en esta baza.
        return replace(estado, manos=(manos[0], manos[1]), mesa=(mesa[0], mesa[1]), turno=rival)

    # Ambos jugaron: resolver la baza.
    c0, c1 = mesa[0], mesa[1]
    assert c0 is not None and c1 is not None  # garantizado por el flujo
    ganador_baza = _ganador_baza(c0, c1)
    bazas = estado.bazas + (ResultadoBaza(cartas=(c0, c1), ganador=ganador_baza),)

    ganador_ronda = _resolver_ronda(bazas, estado.mano)
    if ganador_ronda is not None:
        return replace(
            estado,
            manos=(manos[0], manos[1]),
            mesa=(None, None),
            bazas=bazas,
            ganador=ganador_ronda,
            terminada=True,
            turno=ganador_ronda,
        )

    # La ronda sigue: arranca la próxima baza quien ganó ésta; si fue parda, el mano.
    siguiente = estado.mano if ganador_baza is None else ganador_baza
    return replace(
        estado,
        manos=(manos[0], manos[1]),
        mesa=(None, None),
        bazas=bazas,
        turno=siguiente,
    )


def _ganador_baza(c0: Carta, c1: Carta) -> int | None:
    """Quién gana una baza: 0, 1, o None si es parda (mismo rango)."""
    f0, f1 = fuerza_truco(c0), fuerza_truco(c1)
    if f0 > f1:
        return 0
    if f1 > f0:
        return 1
    return None


def _resolver_ronda(bazas: tuple[ResultadoBaza, ...], mano: int) -> int | None:
    """Ganador de la ronda según las bazas jugadas, o None si aún no se define.

    Implementa la tabla completa de §3 (incluidas las pardas):

    * Gana 2 bazas → ese jugador.
    * Gana una y emparda otra → ese jugador.
    * 1-1 → decide la 3ª; si la 3ª es parda, gana **quien ganó la 1ª baza**.
    * Las 3 pardas → gana **el mano**.
    """
    ganadores = [b.ganador for b in bazas]
    if len(ganadores) < 2:
        return None

    a, b = ganadores[0], ganadores[1]

    # Decisiones al cabo de dos bazas.
    if a is not None and a == b:
        return a  # 2-0
    if a is not None and b is None:
        return a  # gana la 1ª, emparda la 2ª
    if a is None and b is not None:
        return b  # emparda la 1ª, gana la 2ª

    # Queda 1-1 (a, b distintos) o (parda, parda): se define en la 3ª baza.
    if len(ganadores) < 3:
        return None

    c = ganadores[2]
    if a is not None and b is not None:
        # Fue 1-1: gana la 3ª; si la 3ª es parda, gana quien ganó la 1ª.
        return c if c is not None else a
    # Fueron dos pardas: gana la 3ª; si también es parda, gana el mano.
    return c if c is not None else mano
