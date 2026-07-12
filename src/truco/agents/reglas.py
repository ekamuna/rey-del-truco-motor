"""AgenteReglas — el primer bot con criterio (heurísticas, NO es ML).

Referencia: ``docs/DOCUMENTO-MAESTRO.md`` §3 (cómo piensa un buen jugador).

Traduce a código las heurísticas del truco: cuándo cantar envido/truco, cómo
responder, qué carta jugar y cuándo guardar las bravas. Los umbrales son
configurables (:class:`ConfigReglas`) para poder ajustarlo sin tocar la lógica.

Es determinista: mismas condiciones → misma decisión. Eso lo hace testeable y
sirve de línea base contra la cual medir el ML más adelante.
"""

from __future__ import annotations

from dataclasses import dataclass

from truco.agents.base import Agent
from truco.core.acciones import (
    CATEGORIA_ENVIDO,
    Accion,
    TipoAccion,
)
from truco.core.cards import fuerza_truco
from truco.core.state import EstadoObservable

#: Umbral de fuerza para considerar una carta "brava" (1♠,1♣,7♠,7oro = 10..13).
_FUERZA_BRAVA = 10
#: Umbral de fuerza para considerar una carta "alta" (2 o mejor).
_FUERZA_ALTA = 8


@dataclass(frozen=True)
class ConfigReglas:
    """Umbrales ajustables del bot de reglas."""

    cantar_envido: int = 27  # tanto mínimo para cantar envido
    real_envido: int = 31  # tanto para escalar a real envido
    querer_envido: int = 27  # tanto mínimo para querer un envido
    cantar_truco_fuerza: int = _FUERZA_BRAVA  # fuerza de la mejor carta para cantar truco
    querer_truco_fuerza: int = _FUERZA_ALTA  # fuerza para querer un truco


class AgenteReglas(Agent):
    def __init__(self, config: ConfigReglas | None = None) -> None:
        self.cfg = config or ConfigReglas()

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        tipos = {a.tipo for a in acciones}
        # ¿Estoy respondiendo a un canto?
        if obs.pendiente is not None and TipoAccion.QUIERO in tipos:
            if obs.pendiente.categoria == CATEGORIA_ENVIDO:
                decision = self._responder_envido(obs, tipos)
            else:
                decision = self._responder_truco(obs, tipos)
            return self._asegurar(decision, acciones)

        # Mi turno: primero considero cantar; si no, juego una carta.
        cantar = self._considerar_canto(obs, tipos)
        if cantar is not None:
            return self._asegurar(cantar, acciones)
        return self._asegurar(self._elegir_carta(obs), acciones)

    # --- Cantar (mi turno) ---------------------------------------------------

    def _considerar_canto(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion | None:
        # Envido primero (solo se ofrece en la primera baza).
        if TipoAccion.ENVIDO in tipos and obs.mi_tanto >= self.cfg.cantar_envido:
            if obs.mi_tanto >= self.cfg.real_envido and TipoAccion.REAL_ENVIDO in tipos:
                return Accion(TipoAccion.REAL_ENVIDO)
            return Accion(TipoAccion.ENVIDO)
        # Cantar truco con mano fuerte.
        if TipoAccion.TRUCO in tipos and self._fuerza_maxima(obs) >= self.cfg.cantar_truco_fuerza:
            return Accion(TipoAccion.TRUCO)
        # Subir el truco (retruco / vale cuatro) con mano muy fuerte.
        for subir in (TipoAccion.RETRUCO, TipoAccion.VALE_CUATRO):
            if subir in tipos and self._fuerza_maxima(obs) >= _FUERZA_BRAVA + 2:
                return Accion(subir)
        return None

    # --- Responder envido ----------------------------------------------------

    def _responder_envido(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion:
        tanto = obs.mi_tanto
        if tanto >= self.cfg.real_envido and TipoAccion.REAL_ENVIDO in tipos:
            return Accion(TipoAccion.REAL_ENVIDO)
        if tanto >= self.cfg.querer_envido:
            return Accion(TipoAccion.QUIERO)
        return Accion(TipoAccion.NO_QUIERO)

    # --- Responder truco -----------------------------------------------------

    def _responder_truco(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion:
        fuerza = self._fuerza_maxima(obs)
        gane_una = any(b.ganador == obs.jugador for b in obs.bazas)
        if fuerza >= _FUERZA_BRAVA + 2 and TipoAccion.RETRUCO in tipos:
            return Accion(TipoAccion.RETRUCO)
        if fuerza >= self.cfg.querer_truco_fuerza or gane_una:
            return Accion(TipoAccion.QUIERO)
        return Accion(TipoAccion.NO_QUIERO)

    # --- Elegir carta --------------------------------------------------------

    def _elegir_carta(self, obs: EstadoObservable) -> Accion:
        cartas = obs.mi_mano
        rival = obs.mesa[1 - obs.jugador]

        if rival is not None:
            # Respondo a la carta del rival: mínima que gane; si no puedo, la más baja.
            ganadoras = [c for c in cartas if fuerza_truco(c) > fuerza_truco(rival)]
            elegida = (
                min(ganadoras, key=fuerza_truco) if ganadoras else min(cartas, key=fuerza_truco)
            )
            return Accion(TipoAccion.JUGAR, elegida)

        # Soy mano de la baza: si voy perdiendo, juego fuerte; si no, conservo.
        mias = sum(1 for b in obs.bazas if b.ganador == obs.jugador)
        rivales = sum(1 for b in obs.bazas if b.ganador is not None and b.ganador != obs.jugador)
        if len(cartas) == 1 or rivales > mias:
            return Accion(TipoAccion.JUGAR, max(cartas, key=fuerza_truco))
        return Accion(TipoAccion.JUGAR, min(cartas, key=fuerza_truco))

    # --- Helpers -------------------------------------------------------------

    def _fuerza_maxima(self, obs: EstadoObservable) -> int:
        return max((fuerza_truco(c) for c in obs.mi_mano), default=0)

    @staticmethod
    def _asegurar(accion: Accion, acciones: tuple[Accion, ...]) -> Accion:
        """Red de seguridad: si la decisión no fuera legal, cae en algo legal."""
        if accion in acciones:
            return accion
        # Preferir jugar una carta; si no, la primera acción disponible.
        for a in acciones:
            if a.tipo is TipoAccion.JUGAR:
                return a
        return acciones[0]
