"""Abstracción del estado y de las acciones para el agente que aprende.

La clave: convertir el estado (rico) en una **clave chica** para que la tabla Q
sea aprendible, y traducir acciones abstractas (cantar/querer/subir…) a las
concretas del motor.
"""

from __future__ import annotations

from enum import Enum

from truco.core.acciones import CANTOS_ENVIDO, CANTOS_TRUCO, Accion, TipoAccion, jugar_carta
from truco.core.cards import fuerza_truco
from truco.core.state import EstadoObservable

#: Tipo de la clave de estado (todo discreto y chico).
ClaveEstado = tuple[str, int, int, int, int, bool]


class AccionQ(Enum):
    """Acciones abstractas que el agente aprende a valorar."""

    JUGAR = "jugar"  # jugar una carta (cuál, lo decide una heurística fija)
    ENVIDO = "envido"  # cantar envido
    TRUCO = "truco"  # cantar truco
    QUIERO = "quiero"
    NO_QUIERO = "no_quiero"
    SUBIR = "subir"  # subir el canto pendiente (real/falta o retruco/vale cuatro)
    MAZO = "mazo"


# Orden de preferencia al concretar un "subir" (el más fuerte disponible).
_PREF_SUBIR = (
    TipoAccion.FALTA_ENVIDO,
    TipoAccion.REAL_ENVIDO,
    TipoAccion.VALE_CUATRO,
    TipoAccion.RETRUCO,
    TipoAccion.ENVIDO,
)


def clave_estado(obs: EstadoObservable) -> ClaveEstado:
    """Resume lo observable en una clave chica y discreta."""
    if obs.pendiente is None:
        momento = "libre"
    elif obs.pendiente.categoria == "envido":
        momento = "resp_envido"
    else:
        momento = "resp_truco"

    fuerza_max = max((fuerza_truco(c) for c in obs.mi_mano), default=0)
    fuerza = 0 if fuerza_max < 8 else (1 if fuerza_max < 10 else 2)  # floja/media/brava
    tanto = 0 if obs.mi_tanto < 27 else (1 if obs.mi_tanto < 30 else 2)

    mias = sum(1 for b in obs.bazas if b.ganador == obs.jugador)
    rivales = sum(1 for b in obs.bazas if b.ganador is not None and b.ganador != obs.jugador)
    bazas = (mias > rivales) - (mias < rivales)  # -1 perdiendo, 0 parejo, 1 ganando

    return (momento, fuerza, tanto, bazas, obs.nivel_truco, obs.soy_mano)


def acciones_legales_q(obs: EstadoObservable, concretas: tuple[Accion, ...]) -> list[AccionQ]:
    """Acciones abstractas disponibles, derivadas de las concretas del motor."""
    tipos = {a.tipo for a in concretas}
    if obs.pendiente is not None:
        legales = [AccionQ.QUIERO, AccionQ.NO_QUIERO]
        if tipos & set(CANTOS_ENVIDO) or tipos & set(CANTOS_TRUCO):
            legales.append(AccionQ.SUBIR)
        return legales

    legales = [AccionQ.JUGAR]
    if TipoAccion.ENVIDO in tipos:
        legales.append(AccionQ.ENVIDO)
    if tipos & set(CANTOS_TRUCO):
        legales.append(AccionQ.TRUCO)
    legales.append(AccionQ.MAZO)
    return legales


def a_concreta(accion_q: AccionQ, obs: EstadoObservable, concretas: tuple[Accion, ...]) -> Accion:
    """Traduce la acción abstracta a una acción concreta legal del motor."""
    if accion_q is AccionQ.JUGAR:
        return _elegir_carta(obs, concretas)
    if accion_q is AccionQ.QUIERO:
        return Accion(TipoAccion.QUIERO)
    if accion_q is AccionQ.NO_QUIERO:
        return Accion(TipoAccion.NO_QUIERO)
    if accion_q is AccionQ.MAZO:
        return Accion(TipoAccion.MAZO)
    if accion_q is AccionQ.ENVIDO:
        return _buscar(concretas, (TipoAccion.ENVIDO,))
    if accion_q is AccionQ.TRUCO:
        return _buscar(concretas, CANTOS_TRUCO)
    return _buscar(concretas, _PREF_SUBIR)  # SUBIR


def _elegir_carta(obs: EstadoObservable, concretas: tuple[Accion, ...]) -> Accion:
    """Heurística fija de carta: la mínima que gana; si no puede, la más baja."""
    cartas = [a.carta for a in concretas if a.tipo is TipoAccion.JUGAR and a.carta is not None]
    rival = obs.mesa[1 - obs.jugador]
    if rival is not None:
        ganadoras = [c for c in cartas if fuerza_truco(c) > fuerza_truco(rival)]
        elegida = min(ganadoras or cartas, key=fuerza_truco)
    else:
        elegida = min(cartas, key=fuerza_truco)
    return jugar_carta(elegida)


def _buscar(concretas: tuple[Accion, ...], preferencia: tuple[TipoAccion, ...]) -> Accion:
    """Devuelve la primera acción concreta cuyo tipo esté en la preferencia."""
    for tipo in preferencia:
        for accion in concretas:
            if accion.tipo is tipo:
                return accion
    return concretas[0]  # red de seguridad
