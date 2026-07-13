"""AgentePIMC — juega infiriendo las cartas ocultas del rival (Perfect Information
Monte Carlo).

Referencia: ``docs/LECTURA-DEL-RIVAL.md``.

En cada decisión, **imagina K manos posibles** del rival (consistentes con lo que
mostró y con lo que queda en el mazo), simula el resultado en cada una, y vota. Es
el "leer al rival" del experto, automatizado. NUNCA ve las cartas reales del rival.

Usa la **restricción del envido**: si el rival cantó su tanto (público con "quiero"),
solo imagina manos cuyo tanto coincida. No entrena: es búsqueda + inferencia.
"""

from __future__ import annotations

import itertools
import random

from truco.agents.base import Agent
from truco.core.acciones import Accion, TipoAccion, jugar_carta
from truco.core.cards import Carta, baraja, fuerza_truco
from truco.core.engine import acciones_legales, actor, aplicar
from truco.core.scoring import (
    NO_QUIERO_TRUCO,
    VALOR_TRUCO,
    tanto_envido,
    valor_envido_no_querido,
    valor_envido_querido,
    valor_falta_envido,
)
from truco.core.state import EstadoObservable, EstadoRonda, ResultadoBaza

_TODAS = baraja()

# Umbrales de decisión (probabilidad de ganar estimada por muestreo).
_CANTAR = 0.55  # cantar solo con ventaja
_MAX_RECHAZOS = 25  # intentos para muestrear una mano que cumpla la restricción

# Efecto de SELECCIÓN del envido: si el rival CANTA envido, es porque tiene puntos.
# Al responder, sólo imaginamos manos del rival con tanto >= este piso (escalado
# según cante envido / real / falta). Sin esto el PIMC estima con prior uniforme,
# sobreestima su equity y PAGA envidos que debería no querer (fuga medida: -0.135/ronda).
_TANTO_RIVAL_CANTA = 27  # piso base: tanto mínimo asumido cuando el rival canta envido
# (calibrado en el panel: 27 maximiza el promedio; coincide con el percentil ~82 del tanto,
#  el rango donde un rival "canta con puntos". Ver docs/NORTE.md T1 y el análisis de equity.)


class AgentePIMC(Agent):
    """Enumera TODAS las manos posibles del rival (exacto) cuando son pocas; si son
    demasiadas (miles), cae a muestreo Monte Carlo de ``muestras`` manos."""

    def __init__(
        self,
        muestras: int = 80,
        seed: int = 0,
        tope_enumerar: int = 200,
        umbral_cantar: float = _CANTAR,
        tanto_rival_canta_envido: int = _TANTO_RIVAL_CANTA,
    ) -> None:
        self.k = muestras
        self.tope = tope_enumerar
        self.umbral_cantar = umbral_cantar
        self.tanto_rival_canta_envido = tanto_rival_canta_envido
        self._rng = random.Random(seed)

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        tipos = {a.tipo for a in acciones}
        if obs.pendiente is not None and TipoAccion.QUIERO in tipos:
            if obs.pendiente.categoria == "envido":
                if self._prob_gana_envido(obs) >= self._umbral_querer_envido_ev(obs):
                    return self._escalar_o_querer(obs, tipos)  # revira si tengo un monstruo
                return Accion(TipoAccion.NO_QUIERO)
            prob = self._prob_gana_cartas(obs)
            if prob >= self._umbral_querer_truco_ev(obs):
                return self._escalar_o_querer_truco(obs, tipos, prob)
            return Accion(TipoAccion.NO_QUIERO)

        if TipoAccion.ENVIDO in tipos and self._prob_gana_envido(obs) >= self.umbral_cantar:
            return Accion(TipoAccion.ENVIDO)
        if TipoAccion.TRUCO in tipos and self._prob_gana_cartas(obs) >= self.umbral_cantar:
            return Accion(TipoAccion.TRUCO)

        cartas = [a.carta for a in acciones if a.tipo is TipoAccion.JUGAR and a.carta is not None]
        return self._elegir_carta(obs, cartas)

    def _elegir_carta(self, obs: EstadoObservable, cartas: list[Carta]) -> Accion:
        """Política de cartas mejor que 'la mínima que gana' (medida: +0.067/ronda).

        Clave: ``_min_que_gana`` usa ``>`` estricto, así que NUNCA emparda. Pero
        empardar la 1ª baza (aun pudiendo matar) preserva la estructura de la mano y
        me deja de respondedor en la 2ª (parda 1ª + gano 2ª = gano la ronda). De la 2ª
        en adelante, en cambio, hay que cerrar: si puedo ganar, gano."""
        rival = obs.mesa[1 - obs.jugador]
        if rival is None:
            return self._liderar(obs, cartas)
        fr = fuerza_truco(rival)
        matan = [c for c in cartas if fuerza_truco(c) > fr]
        empardan = [c for c in cartas if fuerza_truco(c) == fr]
        pierden = [c for c in cartas if fuerza_truco(c) < fr]
        if len(obs.bazas) == 0:  # baza 1: empardar tiene prioridad sobre matar
            preferencia = (empardan, matan, pierden)
        else:  # baza 2+: cerrar, tomar la baza
            preferencia = (matan, empardan, pierden)
        for grupo in preferencia:
            if grupo:
                return jugar_carta(min(grupo, key=fuerza_truco))
        return jugar_carta(min(cartas, key=fuerza_truco))  # inalcanzable, por completitud

    def _liderar(self, obs: EstadoObservable, cartas: list[Carta]) -> Accion:
        """Qué carta liderar. Con mano FLOJA (ninguna carta fuerte, fuerza≥8) conviene
        **hacer primera**: liderar la MÁS ALTA para ganar la 1ª — con la regla de pardas,
        ganar la 1ª gana la ronda si la 3ª se emparda. Con una carta fuerte, en cambio,
        **slow-play**: liderar la más baja y guardar la fuerte (medido: +0.034/ronda en
        manos flojas; nunca liderar tu única carta fuerte, es el peor error)."""
        if len(obs.bazas) != 0 or len(cartas) < 3:
            return jugar_carta(min(cartas, key=fuerza_truco))  # baza 2+ o pocas: la más baja
        if all(fuerza_truco(c) < 8 for c in cartas):  # mano floja → hacer primera
            return jugar_carta(max(cartas, key=fuerza_truco))
        return jugar_carta(min(cartas, key=fuerza_truco))  # tengo una fuerte → guardarla

    # --- Inferencia por muestreo ---------------------------------------------

    def _prob_gana_cartas(self, obs: EstadoObservable) -> float:
        manos = self._candidatas(obs, self.tope)
        if not manos:
            return 0.5
        ganadas = sum(1 for h in manos if _simula_gana_yo(_estado_simulado(obs, h)))
        return ganadas / len(manos)

    def _prob_gana_envido(self, obs: EstadoObservable) -> float:
        piso = self._piso_tanto_rival(obs)
        manos = self._candidatas(obs, self.tope, piso)
        if not manos and piso is not None:
            manos = self._candidatas(obs, self.tope, None)  # piso incompatible con el reparto
        if not manos:
            return 0.5
        jugadas = _rival_jugadas(obs)
        ganadas = sum(1 for h in manos if _gano_envido(obs, tanto_envido(tuple(jugadas + h))))
        return ganadas / len(manos)

    def _escalar_o_querer(self, obs: EstadoObservable, tipos: set[TipoAccion]) -> Accion:
        """Ya decidí querer el envido; si tengo un tanto muy fuerte, REVIRO/escalo para
        inflar el pozo (control de varianza: la falta sólo con 32-33, donde una falta
        querida casi no se pierde; real con 30-31; revira con 28-29). Ver análisis de equity."""
        t = obs.mi_tanto
        if t >= 32 and TipoAccion.FALTA_ENVIDO in tipos:
            return Accion(TipoAccion.FALTA_ENVIDO)
        if t >= 30 and TipoAccion.REAL_ENVIDO in tipos:
            return Accion(TipoAccion.REAL_ENVIDO)
        if t >= 28 and TipoAccion.ENVIDO in tipos:
            return Accion(TipoAccion.ENVIDO)  # envido-envido (revira)
        return Accion(TipoAccion.QUIERO)

    def _escalar_o_querer_truco(
        self, obs: EstadoObservable, tipos: set[TipoAccion], prob: float
    ) -> Accion:
        """Ya decidí querer el truco; con una mano casi ganada (prob muy alta) ESCALO
        a retruco/vale cuatro para inflar el pozo en vez de flat-call (valor puro que la
        autopsia marcó: nunca subía con monstruos). Umbral alto para no escalar faroles."""
        if prob >= 0.80:
            for subir in (TipoAccion.VALE_CUATRO, TipoAccion.RETRUCO):
                if subir in tipos:
                    return Accion(subir)
        return Accion(TipoAccion.QUIERO)

    def _umbral_querer_truco_ev(self, obs: EstadoObservable) -> float:
        """Break-even EV de aceptar el truco pendiente: aceptar (ganar/perder V) vs irse
        (que regala Pnq al rival) → umbral = 0.5 − Pnq/(2V). Truco 0.25, retruco ~0.17,
        vale cuatro ~0.13. Antes era un 0.34 FIJO → foldeaba trucos +EV (la fuga evitable
        más grande medida en la autopsia, sobre todo contra faroleros)."""
        neg = obs.pendiente
        assert neg is not None
        ultimo = neg.ultimo
        return 0.5 - NO_QUIERO_TRUCO[ultimo] / (2 * VALOR_TRUCO[ultimo])

    def _umbral_querer_envido_ev(self, obs: EstadoObservable) -> float:
        """Umbral de equity para aceptar un envido: el **break-even EV del pote**.
        Aceptar un pote V (ganás/perdés V) frente a un 'no quiero' que regala Pnq se
        justifica si eq > 0.5 − Pnq/(2V). Envido simple → 0.25, real → ~0.30, falta → ~0.47.
        Mucho más fino que un umbral fijo: exige más equity cuanto más grande el pote."""
        neg = obs.pendiente
        assert neg is not None
        valor_falta = valor_falta_envido(obs.puntos_partida, obs.objetivo)
        pote = valor_envido_querido(neg.cantos, valor_falta)
        no_quiero = valor_envido_no_querido(neg.cantos)
        return 0.5 - no_quiero / (2 * pote)

    def _piso_tanto_rival(self, obs: EstadoObservable) -> int | None:
        """Si estoy respondiendo un envido del rival, su tanto mínimo asumido (canta con
        puntos), escalado según envido / envido-envido / real / falta. None si no aplica."""
        neg = obs.pendiente
        if neg is None or neg.categoria != "envido":
            return None
        base = self.tanto_rival_canta_envido
        if TipoAccion.FALTA_ENVIDO in neg.cantos:
            piso = base + 4
        elif TipoAccion.REAL_ENVIDO in neg.cantos:
            piso = base + 3
        elif neg.cantos.count(TipoAccion.ENVIDO) >= 2:  # envido-envido (revirado)
            piso = base + 2
        else:
            piso = base
        return min(piso, 33)

    def _candidatas(
        self, obs: EstadoObservable, tope: int, piso_tanto: int | None = None
    ) -> list[list[Carta]]:
        """TODAS las manos ocultas posibles del rival, consistentes con: lo mostrado,
        el tanto cantado, con QUÉ carta me mató, y (si respondo un envido) con que su
        tanto sea >= ``piso_tanto``. Si superan ``tope``, cae a un muestreo de ``self.k``."""
        pozo = _pozo(obs)
        jugadas = _rival_jugadas(obs)
        faltan = min(obs.cartas_rival, len(pozo))
        intervalos = _intervalos_prohibidos(obs)
        consistentes: list[list[Carta]] = []
        for combo in itertools.combinations(pozo, faltan):
            mano = list(combo)
            if _consistente(obs, mano, jugadas, intervalos) and _cumple_piso(
                jugadas, mano, piso_tanto
            ):
                consistentes.append(mano)
                if len(consistentes) > tope:
                    return [
                        self._muestrear_rival(obs, pozo, intervalos, piso_tanto)
                        for _ in range(self.k)
                    ]
        return consistentes

    def _muestrear_rival(
        self,
        obs: EstadoObservable,
        pozo: list[Carta],
        intervalos: list[tuple[int, int]] | None = None,
        piso_tanto: int | None = None,
    ) -> list[Carta]:
        """Muestrea las cartas ocultas del rival (tanto cantado + con qué me mató + piso)."""
        if intervalos is None:
            intervalos = _intervalos_prohibidos(obs)
        jugadas = _rival_jugadas(obs)
        faltan = min(obs.cartas_rival, len(pozo))
        for _ in range(_MAX_RECHAZOS):
            restante = self._rng.sample(pozo, faltan)
            if _consistente(obs, restante, jugadas, intervalos) and _cumple_piso(
                jugadas, restante, piso_tanto
            ):
                return restante
        return self._rng.sample(pozo, faltan)  # si no encontró, muestra libre


# --- Helpers puros -----------------------------------------------------------


def _intervalos_prohibidos(obs: EstadoObservable) -> list[tuple[int, int]]:
    """Deducción del experto: si LIDERÉ una baza y el rival me la ganó respondiendo
    con la carta X (asumiendo que juega la mínima que gana), sus otras cartas NO
    tienen fuerza estrictamente entre mi carta y X. Devuelve esos intervalos (lo, hi)."""
    yo, rival = obs.jugador, 1 - obs.jugador
    intervalos: list[tuple[int, int]] = []
    lider = obs.mano
    for baza in obs.bazas:
        if lider == yo and baza.ganador == rival:
            f_mia = fuerza_truco(baza.cartas[yo])
            f_rival = fuerza_truco(baza.cartas[rival])
            if f_rival > f_mia:
                intervalos.append((f_mia, f_rival))
        lider = obs.mano if baza.ganador is None else baza.ganador
    return intervalos


def _consistente(
    obs: EstadoObservable,
    mano: list[Carta],
    jugadas: list[Carta],
    intervalos: list[tuple[int, int]],
) -> bool:
    """¿Una mano imaginada es posible? Debe dar el tanto cantado (si lo hay) y no
    tener cartas en los intervalos prohibidos por 'con qué me mató'."""
    if obs.tanto_rival is not None and tanto_envido(tuple(jugadas + mano)) != obs.tanto_rival:
        return False
    return not any(lo < fuerza_truco(c) < hi for c in mano for lo, hi in intervalos)


def _cumple_piso(jugadas: list[Carta], mano: list[Carta], piso_tanto: int | None) -> bool:
    """¿La mano imaginada da al menos ``piso_tanto`` de envido? (None = sin restricción)."""
    if piso_tanto is None:
        return True
    return tanto_envido(tuple(jugadas + mano)) >= piso_tanto


def _gano_envido(obs: EstadoObservable, tanto_rival: int) -> bool:
    """¿Gano el envido con mi tanto contra el del rival? (empate → gana el mano)."""
    return obs.mi_tanto > tanto_rival or (obs.mi_tanto == tanto_rival and obs.soy_mano)


def _min_que_gana(cartas: list[Carta], rival: Carta | None) -> Accion:
    if rival is not None:
        ganadoras = [c for c in cartas if fuerza_truco(c) > fuerza_truco(rival)]
        elegida = min(ganadoras or cartas, key=fuerza_truco)
    else:
        elegida = min(cartas, key=fuerza_truco)
    return jugar_carta(elegida)


def _pozo(obs: EstadoObservable) -> list[Carta]:
    """Cartas que el rival PODRÍA tener (todo lo que no vi)."""
    vistas: set[Carta] = set(obs.mi_mano)
    vistas.update(c for c in obs.mesa if c is not None)
    for baza in obs.bazas:
        vistas.update(baza.cartas)
    return [c for c in _TODAS if c not in vistas]


def _rival_jugadas(obs: EstadoObservable) -> list[Carta]:
    rival = 1 - obs.jugador
    jugadas = [obs.mesa[rival]] if obs.mesa[rival] is not None else []
    jugadas += [baza.cartas[rival] for baza in obs.bazas]
    return [c for c in jugadas if c is not None]


def _estado_simulado(obs: EstadoObservable, rival_restante: list[Carta]) -> EstadoRonda:
    """Reconstruye una ronda con las manos vistas desde mi óptica (yo = jugador 0)."""
    yo = obs.jugador

    def rm(indice: int) -> int:
        return 0 if indice == yo else 1

    bazas = tuple(
        ResultadoBaza(
            cartas=(baza.cartas[yo], baza.cartas[1 - yo]),
            ganador=None if baza.ganador is None else rm(baza.ganador),
        )
        for baza in obs.bazas
    )
    return EstadoRonda(
        puntos_partida=obs.puntos_partida,
        objetivo=obs.objetivo,
        manos=(obs.mi_mano, tuple(rival_restante)),
        mano=rm(obs.mano),
        turno=rm(obs.turno),
        mesa=(obs.mesa[yo], obs.mesa[1 - yo]),
        bazas=bazas,
    )


def _simula_gana_yo(estado: EstadoRonda) -> bool:
    """Juega el resto de la ronda (ambos la mínima que gana) → ¿gano yo (jugador 0)?"""
    e = estado
    for _ in range(30):
        if e.terminada:
            break
        if e.pendiente is not None:
            e = aplicar(e, Accion(TipoAccion.QUIERO))
            continue
        jugador = actor(e)
        cartas: list[Carta] = [
            a.carta
            for a in acciones_legales(e)
            if a.tipo is TipoAccion.JUGAR and a.carta is not None
        ]
        e = aplicar(e, _min_que_gana(cartas, e.mesa[1 - jugador]))
    return e.ganador == 0
