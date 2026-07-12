"""Cálculo de tantos y valores de los cantos.

Referencia: ``docs/REGLAMENTO.md`` §4 (envido) y §5 (truco).

Todo puro: dado el estado relevante, devuelve números. Sin efectos.
"""

from __future__ import annotations

from itertools import combinations

from truco.core.acciones import TipoAccion
from truco.core.cards import Carta, valor_envido

#: Puntos que aporta cada canto de envido al ser querido (la falta se calcula aparte).
VALOR_ENVIDO_CANTO: dict[TipoAccion, int] = {
    TipoAccion.ENVIDO: 2,
    TipoAccion.REAL_ENVIDO: 3,
}
#: Valor del truco querido, por nivel de canto.
VALOR_TRUCO: dict[TipoAccion, int] = {
    TipoAccion.TRUCO: 2,
    TipoAccion.RETRUCO: 3,
    TipoAccion.VALE_CUATRO: 4,
}
#: Puntos que gana el que cantó si el rival dice "no quiero" al truco.
NO_QUIERO_TRUCO: dict[TipoAccion, int] = {
    TipoAccion.TRUCO: 1,
    TipoAccion.RETRUCO: 2,
    TipoAccion.VALE_CUATRO: 3,
}
#: Nivel numérico del truco (para comparar y avanzar).
NIVEL_TRUCO: dict[TipoAccion, int] = {
    TipoAccion.TRUCO: 1,
    TipoAccion.RETRUCO: 2,
    TipoAccion.VALE_CUATRO: 3,
}


def tanto_envido(mano: tuple[Carta, ...]) -> int:
    """Tanto de envido de una mano de 3 cartas (§4).

    Dos cartas del mismo palo: ``20 + sus valores``. Sin par de palo: la carta
    de mayor valor de envido. Máximo posible: 33.
    """
    mejor_par: int | None = None
    for a, b in combinations(mano, 2):
        if a.palo == b.palo:
            valor = 20 + valor_envido(a) + valor_envido(b)
            if mejor_par is None or valor > mejor_par:
                mejor_par = valor
    if mejor_par is not None:
        return mejor_par
    return max((valor_envido(c) for c in mano), default=0)


def valor_falta_envido(puntos_partida: tuple[int, int], objetivo: int) -> int:
    """Falta envido (variante simple): lo que le falta al puntero para ganar (§4)."""
    return max(1, objetivo - max(puntos_partida))


def valor_envido_querido(cantos: tuple[TipoAccion, ...], valor_falta: int) -> int:
    """Puntos en juego si se quiere un envido, dada la cadena de cantos.

    Si la cadena termina en falta envido vale la falta; si no, la suma de los
    cantos acumulados.
    """
    if cantos and cantos[-1] is TipoAccion.FALTA_ENVIDO:
        return valor_falta
    return sum(VALOR_ENVIDO_CANTO[c] for c in cantos)


def valor_envido_no_querido(cantos: tuple[TipoAccion, ...]) -> int:
    """Puntos que gana el que cantó si el rival no quiere el envido (§4).

    Se paga lo acumulado ANTES del último canto (el rechazado); mínimo 1.
    """
    previos = cantos[:-1]
    total = sum(VALOR_ENVIDO_CANTO.get(c, 0) for c in previos)
    return total if total > 0 else 1
