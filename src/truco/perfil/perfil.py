"""PerfilDelRival — la "libreta" con la fama de un jugador.

Referencia: ``docs/PERFIL-DEL-RIVAL.md``.

Cada faceta-en-un-contexto es un contador ``(éxitos, intentos)``. La estimación
usa un prior (Beta-Bernoulli) para no sacar conclusiones de una sola jugada.
El perfil se **actualiza** leyendo la trayectoria de la ronda (cartas reveladas).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from truco.core.acciones import (
    CANTOS_ENVIDO,
    CANTOS_TRUCO,
    CATEGORIA_TRUCO,
    TipoAccion,
)
from truco.core.cards import fuerza_truco
from truco.perfil.facetas import (
    ConfigPerfil,
    Contexto,
    Faceta,
    contexto_del,
)
from truco.trayectoria import Paso

#: Respuestas que cuentan como "enfrentó un truco" para la faceta miedoso.
_RESPUESTAS_A_TRUCO = (
    TipoAccion.QUIERO,
    TipoAccion.NO_QUIERO,
    TipoAccion.RETRUCO,
    TipoAccion.VALE_CUATRO,
)


@dataclass
class PerfilDelRival:
    """Fama acumulada de un usuario. Persistible como diccionario/JSON.

    ``config`` define las aristas del modelado (prior, qué es mano débil, etc.).
    No se persiste: es una decisión de afinado, no dato del jugador.
    """

    usuario: str
    conteos: dict[str, tuple[int, int]] = field(default_factory=dict)
    config: ConfigPerfil = field(default_factory=ConfigPerfil)

    # --- Consulta ------------------------------------------------------------

    def estimar(self, faceta: Faceta, contexto: Contexto) -> float:
        """Probabilidad estimada de la faceta en ese contexto (suavizada por el prior)."""
        exitos, intentos = self.conteos.get(_clave(faceta, contexto), (0, 0))
        return self._suavizar(exitos, intentos)

    def intentos(self, faceta: Faceta, contexto: Contexto) -> int:
        """Cuántas observaciones reales hay (confianza) de esa faceta/contexto."""
        return self.conteos.get(_clave(faceta, contexto), (0, 0))[1]

    def intentos_global(self, faceta: Faceta) -> int:
        """Observaciones de la faceta sumando todos los contextos."""
        return sum(self.conteos.get(_clave(faceta, c), (0, 0))[1] for c in Contexto)

    def estimar_global(self, faceta: Faceta) -> float:
        """Estimación de la faceta agrupando todos los contextos."""
        exitos = sum(self.conteos.get(_clave(faceta, c), (0, 0))[0] for c in Contexto)
        return self._suavizar(exitos, self.intentos_global(faceta))

    def _suavizar(self, exitos: int, intentos: int) -> float:
        alfa, beta = self.config.prior_alfa, self.config.prior_beta
        return (exitos + alfa) / (intentos + alfa + beta)

    # --- Actualización -------------------------------------------------------

    def actualizar(self, rival: int, trayectoria: tuple[Paso, ...]) -> None:
        """Aprende de una ronda ya jugada, modelando al jugador ``rival``."""
        if not trayectoria:
            return

        inicial = trayectoria[0].antes
        mano_rival = inicial.manos[rival]
        fuerza_max = max((fuerza_truco(c) for c in mano_rival), default=0)
        tanto_rival = inicial.tantos[rival]
        contexto = contexto_del(
            inicial.puntos_partida[rival],
            inicial.puntos_partida[1 - rival],
            self.config.umbral_contexto,
        )

        mano_debil = fuerza_max < self.config.fuerza_mano_debil
        tanto_bajo = tanto_rival < self.config.tanto_envido_bajo

        for paso in trayectoria:
            if paso.quien != rival:
                continue
            tipo = paso.accion.tipo
            if tipo in CANTOS_TRUCO:
                self._registrar(Faceta.MENTIROSO_TRUCO, contexto, mano_debil)
            if tipo in CANTOS_ENVIDO:
                self._registrar(Faceta.MENTIROSO_ENVIDO, contexto, tanto_bajo)
            pendiente = paso.antes.pendiente
            if (
                pendiente is not None
                and pendiente.categoria == CATEGORIA_TRUCO
                and tipo in _RESPUESTAS_A_TRUCO
            ):
                self._registrar(Faceta.MIEDOSO, contexto, tipo is TipoAccion.NO_QUIERO)

    def _registrar(self, faceta: Faceta, contexto: Contexto, exito: bool) -> None:
        clave = _clave(faceta, contexto)
        exitos, intentos = self.conteos.get(clave, (0, 0))
        self.conteos[clave] = (exitos + (1 if exito else 0), intentos + 1)

    # --- Serialización -------------------------------------------------------

    def a_dict(self) -> dict[str, object]:
        return {
            "usuario": self.usuario,
            "conteos": {k: list(v) for k, v in self.conteos.items()},
        }

    @classmethod
    def desde_dict(
        cls, datos: dict[str, object], config: ConfigPerfil | None = None
    ) -> PerfilDelRival:
        crudos = datos.get("conteos", {})
        assert isinstance(crudos, dict)
        conteos = {k: (int(v[0]), int(v[1])) for k, v in crudos.items()}
        return cls(
            usuario=str(datos["usuario"]),
            conteos=conteos,
            config=config or ConfigPerfil(),
        )


def _clave(faceta: Faceta, contexto: Contexto) -> str:
    return f"{faceta.value}|{contexto.value}"
