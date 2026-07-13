"""Caza de faroles con memoria — opponent modeling HONESTO del envido.

Referencia: ``docs/ESTUDIO-PARTIDAS.md`` (partido #1) y ``docs/NORTE.md`` (T3).

La idea del experto: "che, me mentiste — me lo guardo, con poco te agarro". El bot
perdía porque foldeaba **todos** los faroles de envido del rival y nunca se adaptaba.
Acá lleva un contador Beta-Bernoulli de con qué frecuencia el rival farolea el envido,
y con eso baja el "piso" con que imagina su tanto (le empieza a pagar).

**Fidelidad (clave):** una mentira SÓLO se conoce si se destapó en un *showdown*
(envido con "quiero" y el tanto mostrado). Si el bot foldea, no aprende nada — como en
la vida real. Por eso hace falta el *mixing* (querer de vez en cuando para ver). Esto
arregla la trampa del ``PerfilDelRival`` viejo, que miraba la mano aunque no se mostrara.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from truco.core.acciones import CANTOS_ENVIDO
from truco.core.engine import tanto_rival_publico
from truco.trayectoria import Paso


@dataclass(frozen=True)
class ConfigCazaFaroles:
    """Aristas de la caza de faroles. ``activar=False`` → el bot es idéntico al actual."""

    activar: bool = False
    umbral_farol_tanto: int = 27  # un envido cantado con tanto menor a esto fue farol
    prior_alfa: float = 1.0  # Beta prior neutro (media 0.5)
    prior_beta: float = 1.0
    # --- ajuste del piso de selección ---
    piso_min: int = 20  # nunca imaginar al rival por debajo de esto
    f_base: float = 0.15  # tasa de farol "normal"; sólo por encima se descuenta
    k_piso: float = 12.0  # cuántos puntos de piso baja un farolero confiable
    n0_confianza: float = 4.0  # shrinkage: observaciones para "media confianza"
    # --- mixing (pagar dudosos para generar showdowns) ---
    p_mixing: float = 0.0  # prob base de pagar un envido dudoso para ver
    margen_dudoso: float = 0.12  # banda de equity por debajo del umbral EV que es "dudosa"
    seed_mixing: int = 0
    mixing_solo_hasta_puntos: int = 12  # no explorar cerca del match-point


@dataclass
class MemoriaFaroles:
    """Contador Beta-Bernoulli de faroles de envido por rival. HONESTO: sólo cuenta
    showdowns (envido con 'quiero' y tanto revelado). Persistible como los perfiles."""

    #: rival_id -> (faroles_destapados, showdowns_totales)
    conteos: dict[str, tuple[int, int]] = field(default_factory=dict)

    def estimar_farol(self, rival_id: str, cfg: ConfigCazaFaroles) -> float:
        exitos, intentos = self.conteos.get(rival_id, (0, 0))
        return (exitos + cfg.prior_alfa) / (intentos + cfg.prior_alfa + cfg.prior_beta)

    def intentos(self, rival_id: str) -> int:
        return self.conteos.get(rival_id, (0, 0))[1]

    def _registrar(self, rival_id: str, mintio: bool) -> None:
        exitos, intentos = self.conteos.get(rival_id, (0, 0))
        self.conteos[rival_id] = (exitos + int(mintio), intentos + 1)

    def observar_ronda(
        self,
        mi_jugador: int,
        trayectoria: tuple[Paso, ...],
        cfg: ConfigCazaFaroles,
        rival_id: str = "rival",
    ) -> None:
        """Aprende de la ronda, pero SÓLO de lo que se destapó (fidelidad)."""
        if not trayectoria:
            return
        rival = 1 - mi_jugador
        final = trayectoria[-1].despues
        if not final.envido_con_quiero:  # sin showdown → sin evidencia (fix de la trampa)
            return
        rival_agredio = any(
            paso.quien == rival and paso.accion.tipo in CANTOS_ENVIDO for paso in trayectoria
        )
        if not rival_agredio:
            return
        tanto_pub = tanto_rival_publico(final, rival)  # reutiliza el filtro del motor
        if tanto_pub is not None:  # reveal exacto: sé su número
            self._registrar(rival_id, tanto_pub < cfg.umbral_farol_tanto)
            return
        # reveal ordinal: el rival cantó y PERDIÓ el envido contra un tanto bajo mío
        mi_tanto = final.tantos[mi_jugador]
        if final.envido_ganador == mi_jugador and mi_tanto <= cfg.umbral_farol_tanto:
            self._registrar(rival_id, True)

    # --- Serialización (misma forma que PerfilDelRival) ---

    def a_dict(self) -> dict[str, object]:
        return {"conteos": {k: list(v) for k, v in self.conteos.items()}}

    @classmethod
    def desde_dict(cls, datos: dict[str, object]) -> MemoriaFaroles:
        crudos = datos.get("conteos", {})
        assert isinstance(crudos, dict)
        conteos = {k: (int(v[0]), int(v[1])) for k, v in crudos.items()}
        return cls(conteos=conteos)
