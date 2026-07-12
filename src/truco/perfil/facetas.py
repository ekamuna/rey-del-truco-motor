"""Facetas del perfil, contextos y parámetros configurables del modelado.

Referencia: ``docs/PERFIL-DEL-RIVAL.md`` §4-§6.

Ojo con el vocabulario: esto no "aprende" en el sentido fuerte; **acumula una
estadística y estima un número**. Todas las "aristas" (qué es una mano débil, el
prior, los umbrales de contexto) son **configurables** en :class:`ConfigPerfil`.
"""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class ConfigPerfil:
    """Todas las aristas ajustables del modelado del rival.

    Cambiar cualquiera de estas afina *cómo se mide* la fama, sin tocar la lógica.
    """

    #: Opinión previa (prior Beta): "mentiras" y "sinceras" imaginarias. Media = α/(α+β).
    prior_alfa: float = 1.5  # con β=3.5 → creencia inicial 30%
    prior_beta: float = 3.5
    #: Cantar truco con la mejor carta por debajo de esta fuerza cuenta como farol.
    #: (fuerza 8 = un 2; por debajo, no hay ni un 2). ← definición a revisar más adelante.
    fuerza_mano_debil: int = 8
    #: Cantar envido con un tanto menor a esto cuenta como farol de envido.
    tanto_envido_bajo: int = 27
    #: Diferencia de puntos para considerar que el jugador va ganando/perdiendo.
    umbral_contexto: int = 3


def contexto_del(mis_puntos: int, puntos_rival: int, umbral: int = 3) -> Contexto:
    """Contexto desde la óptica del jugador modelado, según el marcador."""
    diferencia = mis_puntos - puntos_rival
    if diferencia <= -umbral:
        return Contexto.PERDIENDO
    if diferencia >= umbral:
        return Contexto.GANANDO
    return Contexto.PAREJO
