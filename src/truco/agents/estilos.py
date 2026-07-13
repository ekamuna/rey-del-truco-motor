"""Rivales con estilo — variantes del bot de reglas con distinta personalidad.

Sirven como panel de prueba (¿mi agente le gana a todos los estilos?) y como
oponentes diversos para entrenar. Cada uno es un :class:`AgenteReglas` configurado.
"""

from __future__ import annotations

from truco.agents.reglas import AgenteReglas, ConfigReglas


def agresivo(seed: int | None = None) -> AgenteReglas:
    """Canta y sube con poco; farolea seguido; quiere casi todo."""
    return AgenteReglas(
        ConfigReglas(
            cantar_envido=24,
            real_envido=29,
            querer_envido=22,
            cantar_truco_fuerza=8,
            querer_truco_fuerza=4,
            retruco_fuerza=10,
            frecuencia_farol=0.45,
        ),
        seed=seed,
    )


def mentiroso(seed: int | None = None) -> AgenteReglas:
    """Farolea muchísimo (miente con mano fea a cada rato)."""
    return AgenteReglas(
        ConfigReglas(
            cantar_envido=25,
            querer_envido=24,
            cantar_truco_fuerza=9,
            querer_truco_fuerza=6,
            frecuencia_farol=0.7,
            farol_envido_min=18,
        ),
        seed=seed,
    )


def conservador(seed: int | None = None) -> AgenteReglas:
    """Solo apuesta con manos buenas; nunca farolea; no quiere si duda."""
    return AgenteReglas(
        ConfigReglas(
            cantar_envido=30,
            real_envido=32,
            querer_envido=29,
            cantar_truco_fuerza=12,
            querer_truco_fuerza=10,
            retruco_fuerza=13,
            frecuencia_farol=0.0,
        ),
        seed=seed,
    )
