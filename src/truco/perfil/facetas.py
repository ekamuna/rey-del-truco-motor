"""Facetas del perfil, contextos y constantes del modelado.

Referencia: ``docs/PERFIL-DEL-RIVAL.md`` §4-§6.
"""

from __future__ import annotations

from enum import Enum


class Faceta(Enum):
    """Las dimensiones del perfil que estimamos (v1)."""

    MENTIROSO_TRUCO = "mentiroso_truco"  # P(mano débil | cantó truco)
    MENTIROSO_ENVIDO = "mentiroso_envido"  # P(tanto bajo | cantó envido)
    MIEDOSO = "miedoso"  # P(no quiero | le cantaron truco)


class Contexto(Enum):
    """El momento del partido en que ocurre la jugada (desde la óptica del rival)."""

    GANANDO = "ganando"
    PAREJO = "parejo"
    PERDIENDO = "perdiendo"


#: Prior neutral (creencia inicial ~30%, con peso de ~5 observaciones). Evita que
#: una sola jugada dé "100% mentiroso". Modelo Beta-Bernoulli: media = α/(α+β).
PRIOR_ALFA = 1.5
PRIOR_BETA = 3.5

#: Una mano es "débil" para el truco si su mejor carta no llega a un 2 (fuerza < 8).
FUERZA_MANO_DEBIL = 8
#: Un tanto de envido es "bajo" si es menor a esto.
TANTO_ENVIDO_BAJO = 27
#: Diferencia de puntos para considerar que un jugador va ganando/perdiendo.
UMBRAL_CONTEXTO = 3


def contexto_del(mis_puntos: int, puntos_rival: int) -> Contexto:
    """Contexto desde la óptica del jugador modelado, según el marcador."""
    diferencia = mis_puntos - puntos_rival
    if diferencia <= -UMBRAL_CONTEXTO:
        return Contexto.PERDIENDO
    if diferencia >= UMBRAL_CONTEXTO:
        return Contexto.GANANDO
    return Contexto.PAREJO
