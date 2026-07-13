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
from truco.core.scoring import tanto_envido
from truco.core.state import EstadoRonda
from truco.trayectoria import Paso


def _tanto_visible(final: EstadoRonda, rival: int) -> int | None:
    """Tanto del rival que un humano PODRÍA conocer: el mostrado en un showdown de
    envido, o el computado de sus 3 cartas si se jugaron todas (round a 3 bazas)."""
    tanto_pub = tanto_rival_publico(final, rival)
    if tanto_pub is not None:
        return tanto_pub
    cartas = [baza.cartas[rival] for baza in final.bazas]
    if len(cartas) == 3:  # se vieron las 3 → tanto honestamente calculable
        return tanto_envido(tuple(cartas))
    return None


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
    # --- faceta PESCADOR y Regla 1 (el mano que no canta el envido) ---
    umbral_pesca_tanto: int = 26  # el mano que no canta y tiene >= esto, pescó
    value_cant_default: int = 26  # value-cant al mano que pasó: default seguro (vs pescador)
    value_cant_explota: int = 23  # confirmado NO pescador: bajo la vara y exploto


@dataclass
class MemoriaFaroles:
    """Contador Beta-Bernoulli de faroles de envido por rival. HONESTO: sólo cuenta
    showdowns (envido con 'quiero' y tanto revelado). Persistible como los perfiles."""

    #: rival_id -> (faroles_destapados, showdowns_totales)
    conteos: dict[str, tuple[int, int]] = field(default_factory=dict)
    #: rival_id -> (pescas, oportunidades_de_mano_sin_cantar_con_tanto_visible)
    pescas: dict[str, tuple[int, int]] = field(default_factory=dict)

    def estimar_farol(self, rival_id: str, cfg: ConfigCazaFaroles) -> float:
        exitos, intentos = self.conteos.get(rival_id, (0, 0))
        return (exitos + cfg.prior_alfa) / (intentos + cfg.prior_alfa + cfg.prior_beta)

    def intentos(self, rival_id: str) -> int:
        return self.conteos.get(rival_id, (0, 0))[1]

    def estimar_pesca(self, rival_id: str, cfg: ConfigCazaFaroles) -> float:
        exitos, intentos = self.pescas.get(rival_id, (0, 0))
        return (exitos + cfg.prior_alfa) / (intentos + cfg.prior_alfa + cfg.prior_beta)

    def intentos_pesca(self, rival_id: str) -> int:
        return self.pescas.get(rival_id, (0, 0))[1]

    def _registrar(self, rival_id: str, mintio: bool) -> None:
        exitos, intentos = self.conteos.get(rival_id, (0, 0))
        self.conteos[rival_id] = (exitos + int(mintio), intentos + 1)

    def _registrar_pesca(self, rival_id: str, pesco: bool) -> None:
        exitos, intentos = self.pescas.get(rival_id, (0, 0))
        self.pescas[rival_id] = (exitos + int(pesco), intentos + 1)

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
        inicial = trayectoria[0].antes
        final = trayectoria[-1].despues
        rival_canto_envido = any(
            paso.quien == rival and paso.accion.tipo in CANTOS_ENVIDO for paso in trayectoria
        )
        self._aprender_pesca(rival, rival_canto_envido, inicial, final, cfg, rival_id)
        self._aprender_farol(mi_jugador, rival, rival_canto_envido, final, cfg, rival_id)

    def _aprender_farol(
        self,
        mi_jugador: int,
        rival: int,
        rival_canto_envido: bool,
        final: EstadoRonda,
        cfg: ConfigCazaFaroles,
        rival_id: str,
    ) -> None:
        """Faceta FAROLERO: cantó el envido con tanto bajo. Sólo showdowns."""
        if not final.envido_con_quiero or not rival_canto_envido:
            return  # sin showdown, o el rival no fue el agresor → sin evidencia
        tanto_pub = tanto_rival_publico(final, rival)  # reutiliza el filtro del motor
        if tanto_pub is not None:  # reveal exacto: sé su número
            self._registrar(rival_id, tanto_pub < cfg.umbral_farol_tanto)
            return
        # reveal ordinal: el rival cantó y PERDIÓ el envido contra un tanto bajo mío
        mi_tanto = final.tantos[mi_jugador]
        if final.envido_ganador == mi_jugador and mi_tanto <= cfg.umbral_farol_tanto:
            self._registrar(rival_id, True)

    def _aprender_pesca(
        self,
        rival: int,
        rival_canto_envido: bool,
        inicial: EstadoRonda,
        final: EstadoRonda,
        cfg: ConfigCazaFaroles,
        rival_id: str,
    ) -> None:
        """Faceta PESCADOR: el mano NO cantó el envido teniendo puntos (26+) para
        trampear. Se registra sólo si el tanto del mano quedó VISIBLE honestamente
        (showdown de envido, o las 3 cartas jugadas)."""
        if inicial.mano != rival or rival_canto_envido:
            return  # sólo cuando el rival era mano y no inició el envido
        tanto = _tanto_visible(final, rival)
        if tanto is not None:
            self._registrar_pesca(rival_id, tanto >= cfg.umbral_pesca_tanto)

    # --- Serialización (misma forma que PerfilDelRival) ---

    def a_dict(self) -> dict[str, object]:
        return {
            "conteos": {k: list(v) for k, v in self.conteos.items()},
            "pescas": {k: list(v) for k, v in self.pescas.items()},
        }

    @classmethod
    def desde_dict(cls, datos: dict[str, object]) -> MemoriaFaroles:
        def _leer(clave: str) -> dict[str, tuple[int, int]]:
            crudos = datos.get(clave, {})
            assert isinstance(crudos, dict)
            return {k: (int(v[0]), int(v[1])) for k, v in crudos.items()}

        return cls(conteos=_leer("conteos"), pescas=_leer("pescas"))
