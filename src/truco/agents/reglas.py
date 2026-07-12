"""AgenteReglas — el primer bot con criterio (heurísticas, NO es ML).

Referencia: ``docs/DOCUMENTO-MAESTRO.md`` §3 y ``docs/PERFIL-DEL-RIVAL.md``.

Traduce a código las heurísticas del truco: cuándo cantar envido/truco, cómo
responder, qué carta jugar y cuándo guardar las bravas. Los umbrales son
configurables (:class:`ConfigReglas`).

Si se le pasa un :class:`PerfilDelRival`, **ajusta esos umbrales según la fama
del rival**: le acepta el truco/envido con manos más flojas si es mentiroso, y
lo farolea más si es miedoso. Sigue siendo determinista e interpretable.
"""

from __future__ import annotations

from dataclasses import dataclass

from truco.agents.base import Agent
from truco.core.acciones import CATEGORIA_ENVIDO, Accion, TipoAccion
from truco.core.cards import fuerza_truco
from truco.core.state import EstadoObservable
from truco.perfil import Contexto, Faceta, PerfilDelRival
from truco.perfil.facetas import contexto_del
from truco.trayectoria import Paso


@dataclass(frozen=True)
class ConfigReglas:
    """Todas las aristas ajustables del bot: umbrales base + ajuste por perfil."""

    # --- Umbrales base (sin mirar el perfil) ---
    cantar_envido: int = 27  # tanto mínimo para cantar envido
    real_envido: int = 31  # tanto para escalar a real envido
    querer_envido: int = 27  # tanto mínimo para querer un envido
    cantar_truco_fuerza: int = 10  # fuerza de la mejor carta para cantar truco (una brava)
    querer_truco_fuerza: int = 8  # fuerza para querer un truco (un 2 o mejor)
    retruco_fuerza: int = 12  # fuerza para subir a retruco / vale cuatro
    # --- Ajuste por el perfil del rival (0 = ignorar el perfil) ---
    ancla_perfil: float = 0.30  # punto neutro (media del prior): con esto no se ajusta
    k_aceptar_truco: int = 8  # cuánto baja el umbral vs un mentiroso de truco
    k_aceptar_envido: int = 12  # ídem para el envido
    k_farolear_truco: int = 6  # cuánto baja el umbral para farolear a un miedoso


class AgenteReglas(Agent):
    def __init__(
        self,
        config: ConfigReglas | None = None,
        perfil: PerfilDelRival | None = None,
    ) -> None:
        self.cfg = config or ConfigReglas()
        self.perfil = perfil

    # --- Observación del rival (acumula estadística; no "aprende" en el sentido fuerte) ---

    def observar_ronda(self, mi_jugador: int, trayectoria: tuple[Paso, ...]) -> None:
        if self.perfil is not None:
            self.perfil.actualizar(1 - mi_jugador, trayectoria)

    # --- Decisión ------------------------------------------------------------

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        tipos = {a.tipo for a in acciones}
        if obs.pendiente is not None and TipoAccion.QUIERO in tipos:
            if obs.pendiente.categoria == CATEGORIA_ENVIDO:
                decision = self._responder_envido(obs, tipos)
            else:
                decision = self._responder_truco(obs, tipos)
            return self._asegurar(decision, acciones)

        cantar = self._considerar_canto(obs, tipos)
        if cantar is not None:
            return self._asegurar(cantar, acciones)
        return self._asegurar(self._elegir_carta(obs), acciones)

    # --- Cantar (mi turno) ---------------------------------------------------

    def _considerar_canto(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion | None:
        if TipoAccion.ENVIDO in tipos and obs.mi_tanto >= self.cfg.cantar_envido:
            if obs.mi_tanto >= self.cfg.real_envido and TipoAccion.REAL_ENVIDO in tipos:
                return Accion(TipoAccion.REAL_ENVIDO)
            return Accion(TipoAccion.ENVIDO)
        # Cantar truco: con mano fuerte, o farolear si el rival es miedoso.
        if TipoAccion.TRUCO in tipos and self._fuerza_maxima(obs) >= self._umbral_cantar_truco(obs):
            return Accion(TipoAccion.TRUCO)
        for subir in (TipoAccion.RETRUCO, TipoAccion.VALE_CUATRO):
            if subir in tipos and self._fuerza_maxima(obs) >= self.cfg.retruco_fuerza:
                return Accion(subir)
        return None

    # --- Responder envido ----------------------------------------------------

    def _responder_envido(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion:
        tanto = obs.mi_tanto
        if tanto >= self.cfg.real_envido and TipoAccion.REAL_ENVIDO in tipos:
            return Accion(TipoAccion.REAL_ENVIDO)
        if tanto >= self._umbral_querer_envido(obs):
            return Accion(TipoAccion.QUIERO)
        return Accion(TipoAccion.NO_QUIERO)

    # --- Responder truco -----------------------------------------------------

    def _responder_truco(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion:
        fuerza = self._fuerza_maxima(obs)
        gane_una = any(b.ganador == obs.jugador for b in obs.bazas)
        if fuerza >= self.cfg.retruco_fuerza and TipoAccion.RETRUCO in tipos:
            return Accion(TipoAccion.RETRUCO)
        if fuerza >= self._umbral_querer_truco(obs) or gane_una:
            return Accion(TipoAccion.QUIERO)
        return Accion(TipoAccion.NO_QUIERO)

    # --- Umbrales efectivos (ajustados por el perfil) ------------------------

    def _umbral_querer_truco(self, obs: EstadoObservable) -> int:
        # Rival mentiroso en el truco → le acepto con manos más flojas.
        ajuste = self._peso(obs, Faceta.MENTIROSO_TRUCO, self.cfg.k_aceptar_truco)
        return max(0, self.cfg.querer_truco_fuerza - ajuste)

    def _umbral_querer_envido(self, obs: EstadoObservable) -> int:
        ajuste = self._peso(obs, Faceta.MENTIROSO_ENVIDO, self.cfg.k_aceptar_envido)
        return max(0, self.cfg.querer_envido - ajuste)

    def _umbral_cantar_truco(self, obs: EstadoObservable) -> int:
        # Rival miedoso → bajo el listón para cantar (lo faroleo).
        ajuste = self._peso(obs, Faceta.MIEDOSO, self.cfg.k_farolear_truco)
        return max(0, self.cfg.cantar_truco_fuerza - ajuste)

    def _peso(self, obs: EstadoObservable, faceta: Faceta, k: int) -> int:
        """Cuánto correr un umbral según una faceta del rival (0 si no hay perfil)."""
        if self.perfil is None:
            return 0
        contexto = self._contexto(obs)
        tasa = self.perfil.estimar(faceta, contexto)
        return round(k * max(0.0, tasa - self.cfg.ancla_perfil))

    def _contexto(self, obs: EstadoObservable) -> Contexto:
        rival = 1 - obs.jugador
        umbral = self.perfil.config.umbral_contexto if self.perfil is not None else 3
        return contexto_del(obs.puntos_partida[rival], obs.puntos_partida[obs.jugador], umbral)

    # --- Elegir carta --------------------------------------------------------

    def _elegir_carta(self, obs: EstadoObservable) -> Accion:
        cartas = obs.mi_mano
        rival = obs.mesa[1 - obs.jugador]

        if rival is not None:
            ganadoras = [c for c in cartas if fuerza_truco(c) > fuerza_truco(rival)]
            elegida = (
                min(ganadoras, key=fuerza_truco) if ganadoras else min(cartas, key=fuerza_truco)
            )
            return Accion(TipoAccion.JUGAR, elegida)

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
        if accion in acciones:
            return accion
        for a in acciones:
            if a.tipo is TipoAccion.JUGAR:
                return a
        return acciones[0]
