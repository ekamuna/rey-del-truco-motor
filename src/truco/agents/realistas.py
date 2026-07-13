"""Rivales realistas para el examen del bot — con lógica de decisión de verdad,
no faroleo al voleo. El bot NO sabe a cuál enfrenta. Referencia: ``docs/NORTE.md`` T4.

- :class:`AgenteMentiroso` — te **calcula**: farolea sólo cuando huele tu debilidad.
- :class:`AgenteEstratega` — te **induce**: slow-play y pesca para que cantes y revirarte.

Conservador y agresivo son recalibraciones de :class:`AgenteReglas` (ver factories).
"""

from __future__ import annotations

from truco.agents._senales import (
    debilidad_rival,
    es_premium,
    fuerza_max,
    n_bravas,
    rival_paso_envido,
)
from truco.agents.reglas import AgenteReglas, ConfigReglas
from truco.core.acciones import CANTOS_ENVIDO, Accion, TipoAccion
from truco.core.cards import fuerza_truco
from truco.core.state import EstadoObservable


class AgenteMentiroso(AgenteReglas):
    """Farolea **condicional a la debilidad leída** del rival (no un RNG al voleo):
    si el rival pasó el envido o tiró carta baja, huele que está flojo y ataca; si el
    rival mostró fuerza, juega honesto. Y le paga el farol al que lo agrede débil."""

    def _considerar_canto(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion | None:
        honesto = super()._considerar_canto(obs, tipos)
        if honesto is not None:
            return honesto
        if debilidad_rival(obs) >= 0.5:
            # Farol de truco robando a un rival que se muestra débil.
            if TipoAccion.TRUCO in tipos and fuerza_max(obs) < self.cfg.cantar_truco_fuerza:
                return Accion(TipoAccion.TRUCO)
            # Semi-farol de envido: él pasó el envido (tanto bajo) y yo tengo algo medio.
            if (
                rival_paso_envido(obs)
                and TipoAccion.ENVIDO in tipos
                and 20 <= obs.mi_tanto < self.cfg.cantar_envido
            ):
                return Accion(TipoAccion.ENVIDO)
        return None

    def _responder_truco(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion:
        # Si el rival cantó truco pero venía mostrando debilidad, le pago el farol.
        if debilidad_rival(obs) >= 0.5 and TipoAccion.QUIERO in tipos and fuerza_max(obs) >= 5:
            return Accion(TipoAccion.QUIERO)
        return super()._responder_truco(obs, tipos)


class AgenteEstratega(AgenteReglas):
    """Induce al rival: **slow-play** (lidera bajo teniendo bravas para representar
    debilidad) y **pesca** (no canta teniendo, para que cante el rival y revirarle)."""

    def _considerar_canto(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion | None:
        honesto = super()._considerar_canto(obs, tipos)
        if honesto is None:
            return None
        primera_baza = len(obs.bazas) == 0
        tiene_trampa = n_bravas(obs) >= 2 or fuerza_max(obs) >= 12
        # Slow-play: no cantar truco en la 1ª teniendo trampa (dejar que cante el rival).
        if honesto.tipo is TipoAccion.TRUCO and tiene_trampa and primera_baza:
            return None
        # Pescar el envido: con un monstruo (31+) no canto, espero revirar.
        if honesto.tipo in CANTOS_ENVIDO and obs.mi_tanto >= 31:
            return None
        return honesto

    def _responder_truco(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion:
        # Mordió el anzuelo: cantó truco y yo tengo la trampa → revira.
        tiene_trampa = n_bravas(obs) >= 2 or fuerza_max(obs) >= 11
        if tiene_trampa and TipoAccion.RETRUCO in tipos:
            return Accion(TipoAccion.RETRUCO)
        return super()._responder_truco(obs, tipos)

    def _elegir_carta(self, obs: EstadoObservable) -> Accion:
        lidero_primera = len(obs.bazas) == 0 and obs.mesa[0] is None and obs.mesa[1] is None
        if es_premium(obs) and lidero_primera:
            # Representar debilidad: liderar con la más baja guardando las bravas.
            return Accion(TipoAccion.JUGAR, min(obs.mi_mano, key=fuerza_truco))
        return super()._elegir_carta(obs)


# --- Factories del panel realista -------------------------------------------


def conservador_real(seed: int | None = None) -> AgenteReglas:
    """Sólo apuesta con manos muy buenas; nunca farolea; foldea si duda."""
    return AgenteReglas(
        ConfigReglas(
            cantar_envido=31,
            real_envido=32,
            querer_envido=29,
            cantar_truco_fuerza=12,
            querer_truco_fuerza=10,
            retruco_fuerza=13,
            frecuencia_farol=0.0,
        ),
        seed=seed,
    )


def agresivo_real(seed: int | None = None) -> AgenteReglas:
    """No le importa perder: canta y sube con poco, quiere casi todo."""
    return AgenteReglas(
        ConfigReglas(
            cantar_envido=24,
            real_envido=29,
            querer_envido=22,
            cantar_truco_fuerza=7,
            querer_truco_fuerza=4,
            retruco_fuerza=9,
            frecuencia_farol=0.45,
        ),
        seed=seed,
    )


def mentiroso_real(seed: int | None = None) -> AgenteMentiroso:
    """Te calcula y miente con propósito (farol condicional, frecuencia_farol=0)."""
    return AgenteMentiroso(
        ConfigReglas(
            cantar_envido=27,
            querer_envido=25,
            cantar_truco_fuerza=10,
            querer_truco_fuerza=7,
            frecuencia_farol=0.0,
        ),
        seed=seed,
    )


def estratega_real(seed: int | None = None) -> AgenteEstratega:
    """Slow-play y pesca para inducirte y revirarte."""
    return AgenteEstratega(
        ConfigReglas(
            cantar_envido=27,
            querer_envido=26,
            cantar_truco_fuerza=10,
            querer_truco_fuerza=8,
            retruco_fuerza=11,
            frecuencia_farol=0.0,
        ),
        seed=seed,
    )
