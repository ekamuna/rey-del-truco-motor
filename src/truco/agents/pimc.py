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
from math import comb

from truco.agents._senales import rival_paso_envido
from truco.agents.base import Agent
from truco.agents.memoria_faroles import ConfigCazaFaroles, MemoriaFaroles
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
from truco.trayectoria import Paso

_TODAS = baraja()

# Umbrales de decisión (probabilidad de ganar estimada por muestreo).
_CANTAR = 0.55  # cantar solo con ventaja
_MAX_RECHAZOS = 25  # intentos para muestrear una mano que cumpla la restricción

# Truco = se gana con 2 bazas (teoría del experto, docs/LOGICA-TRUCO.md).
_FUERTE = 8  # fuerza de una carta "ganadora" (2, 3 o brava): gana la mayoría de las bazas
_P_ESCALAR = 0.10  # sólo escalo (retruco/vale4) si P(el rival me supere) < esto (>90% seguro)

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
        memoria: MemoriaFaroles | None = None,
        config_caza: ConfigCazaFaroles | None = None,
        rival_id: str = "rival",
    ) -> None:
        self.k = muestras
        self.tope = tope_enumerar
        self.umbral_cantar = umbral_cantar
        self.tanto_rival_canta_envido = tanto_rival_canta_envido
        self._rng = random.Random(seed)
        self.cfg_caza = config_caza or ConfigCazaFaroles()
        self.memoria = memoria if memoria is not None else MemoriaFaroles()
        self.rival_id = rival_id
        self._rng_mix = random.Random(self.cfg_caza.seed_mixing)  # SEPARADO del muestreo

    def observar_ronda(self, mi_jugador: int, trayectoria: tuple[Paso, ...]) -> None:
        """Aprende los faroles de envido del rival (sólo si la caza está activada)."""
        if self.cfg_caza.activar:
            self.memoria.observar_ronda(mi_jugador, trayectoria, self.cfg_caza, self.rival_id)

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        tipos = {a.tipo for a in acciones}
        if obs.pendiente is not None and TipoAccion.QUIERO in tipos:
            if obs.pendiente.categoria == "envido":
                eq = self._prob_gana_envido(obs)
                if eq >= self._umbral_querer_envido_ev(obs):
                    return self._escalar_o_querer(obs, tipos)  # revira si tengo un monstruo
                if self._debo_explorar(obs, eq):  # pago un dudoso para verle el farol
                    return Accion(TipoAccion.QUIERO)
                return Accion(TipoAccion.NO_QUIERO)
            prob = self._prob_gana_cartas(obs)
            if prob >= self._umbral_querer_truco_ev(obs):
                return self._escalar_o_querer_truco(obs, tipos, prob)
            return Accion(TipoAccion.NO_QUIERO)

        if TipoAccion.ENVIDO in tipos and self._value_cant_mano_paso(obs):
            return Accion(TipoAccion.ENVIDO)  # Regla 1: el mano pasó → está flojo, le cobro
        if TipoAccion.ENVIDO in tipos and self._prob_gana_envido(obs) >= self.umbral_cantar:
            return Accion(TipoAccion.ENVIDO)
        if (
            TipoAccion.TRUCO in tipos
            and self._estructura_para_cantar_truco(obs)
            and self._prob_gana_cartas(obs) >= self.umbral_cantar
        ):
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
        if self._lidero_baza_decisiva(obs):  # FIX D: tras parda, la baza que lidero DEFINE
            return jugar_carta(max(cartas, key=fuerza_truco))  # → liderar la MÁS ALTA para ganarla
        if len(obs.bazas) != 0 or len(cartas) < 3:
            return jugar_carta(min(cartas, key=fuerza_truco))  # baza 2+ o pocas: la más baja
        if all(fuerza_truco(c) < 8 for c in cartas):  # mano floja → hacer primera
            return jugar_carta(max(cartas, key=fuerza_truco))
        return jugar_carta(min(cartas, key=fuerza_truco))  # tengo una fuerte → guardarla

    def _lidero_baza_decisiva(self, obs: EstadoObservable) -> bool:
        """¿La baza que estoy por LIDERAR define la mano? (FIX D) Tras una parda con las
        bazas parejas, el que gana la próxima gana la mano → hay que liderar la MÁS ALTA
        (no la más baja). Sin esto, tras una parda el bot regalaba manos ganadas liderando
        su peor carta en la baza decisiva (error medido, docs/LOGICA-TRUCO.md)."""
        g, p = self._bazas_ganadas(obs)
        hubo_parda = any(b.ganador is None for b in obs.bazas)
        return hubo_parda and g == p

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
        """Ya decidí querer el truco; ESCALO a retruco/vale4 SÓLO con la regla del experto
        (docs/LOGICA-TRUCO.md): >90% seguro = a lo sumo 1 carta sin ver le gana a mi mejor
        carta (conteo hipergeométrico exacto), y con estructura de 2 bazas (voy adelante/
        parejo). Antes era un ``prob>=0.80`` que el slow-play del rival inflaba → farol de
        vale4 con un 3 (que 4 cartas superan). Si no, flat-call (quiero)."""
        g, p = self._bazas_ganadas(obs)
        mejor = max(obs.mi_mano, key=fuerza_truco) if obs.mi_mano else None
        seguro = mejor is not None and self._p_rival_supera(obs, mejor) < _P_ESCALAR
        if prob >= 0.80 and seguro and g >= p and self._estructura_para_cantar_truco(obs):
            for subir in (TipoAccion.VALE_CUATRO, TipoAccion.RETRUCO):
                if subir in tipos:
                    return Accion(subir)
        return Accion(TipoAccion.QUIERO)

    def _bazas_ganadas(self, obs: EstadoObservable) -> tuple[int, int]:
        """(bazas que gané, bazas que perdí) hasta ahora; las pardas no cuentan."""
        yo = obs.jugador
        g = sum(1 for b in obs.bazas if b.ganador == yo)
        p = sum(1 for b in obs.bazas if b.ganador is not None and b.ganador != yo)
        return g, p

    def _p_rival_supera(self, obs: EstadoObservable, mi_carta: Carta) -> float:
        """P(el rival tenga ≥1 carta que le gane a ``mi_carta``), por conteo exacto
        (hipergeométrica) sobre las cartas sin ver y cuántas le quedan al rival. La base
        del vale4: al arranque sólo macho/hembra dan <10%; en la baza decisiva casi
        cualquier brava. Ver docs/LOGICA-TRUCO.md, tabla de equity."""
        pozo = _pozo(obs)
        n = len(pozo)
        r = min(obs.cartas_rival, n)
        k = sum(1 for c in pozo if fuerza_truco(c) > fuerza_truco(mi_carta))
        if r == 0 or k == 0:
            return 0.0
        if n - k < r:
            return 1.0
        return 1.0 - comb(n - k, r) / comb(n, r)

    def _estructura_para_cantar_truco(self, obs: EstadoObservable) -> bool:
        """El truco se gana con 2 bazas → sólo lo canto/escalo con estructura para ganarlas:
        ya gané 2, o gané ≥ las que perdí y me queda una carta FUERTE, o (baza 1) tengo ≥2
        cartas fuertes. Nunca con '1 carta + basura' (el farol que sangraba puntos)."""
        g, p = self._bazas_ganadas(obs)
        if g >= 2:
            return True
        fuertes = sum(1 for c in obs.mi_mano if fuerza_truco(c) >= _FUERTE)
        if len(obs.bazas) == 0:  # baza 1: exijo DOS ganadores
            return fuertes >= 2
        return g >= p and fuertes >= 1  # gano/parejo en bazas + una carta real

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
        piso = min(piso, 33)
        return self._piso_ajustado_por_faroles(piso)

    def _piso_ajustado_por_faroles(self, piso: int) -> int:
        """Baja el piso según la fama del rival: si farolea/canta el envido seguido, imagino
        manos suyas más débiles y le PAGO lo que hoy foldearía. Dos señales, tomo la más
        fuerte: (1) FAROLES destapados (fiel, pero necesita showdowns); (2) FRECUENCIA de
        canto (Target #1: sin showdown — cantar el 50% implica rango ancho → arregla el
        over-fold del 26 ganador). Gradual (Beta + shrinkage): sin evidencia no cambia nada."""
        c = self.cfg_caza
        if not c.activar:
            return piso
        f = self.memoria.estimar_farol(self.rival_id, c)
        n = self.memoria.intentos(self.rival_id)
        desc_farol = c.k_piso * (n / (n + c.n0_confianza)) * max(0.0, f - c.f_base)
        q = self.memoria.frecuencia_canto(self.rival_id, c)
        nq = self.memoria.intentos_canto(self.rival_id)
        desc_freq = c.k_piso * (nq / (nq + c.n0_confianza)) * max(0.0, q - c.f_base_canto)
        return max(c.piso_min, piso - round(max(desc_farol, desc_freq)))

    def _debo_explorar(self, obs: EstadoObservable, eq: float) -> bool:
        """Mixing: pagar un envido DUDOSO (cerca del break-even) de vez en cuando para
        generar un showdown y aprender si el rival farolea — sin esto la memoria nunca
        arranca (foldear no destapa nada). Decae con la confianza; nunca en falta ni cerca
        del match-point (una macana ahí cuesta la partida)."""
        c = self.cfg_caza
        neg = obs.pendiente
        if not c.activar or c.p_mixing <= 0.0 or neg is None:
            return False
        umbral = self._umbral_querer_envido_ev(obs)
        if not (umbral - c.margen_dudoso <= eq < umbral):  # sólo la banda dudosa
            return False
        if TipoAccion.FALTA_ENVIDO in neg.cantos:
            return False
        if max(obs.puntos_partida) >= c.mixing_solo_hasta_puntos:
            return False
        n = self.memoria.intentos(self.rival_id)
        p_efectiva = c.p_mixing * (1.0 - n / (n + c.n0_confianza))  # explora menos al saber
        return self._rng_mix.random() < p_efectiva

    def _value_cant_mano_paso(self, obs: EstadoObservable) -> bool:
        """Regla 1 (docs/MODELADO-DEL-RIVAL.md): si el rival (mano) jugó una carta SIN
        cantar el envido, casi siempre está flojo → cantale de VALOR (no es farol). Umbral
        seguro 26 por defecto (aguanta a un pescador); si confirmé que NO pesca, bajo la
        vara a 23 y exploto. Sólo con el modelado del rival activado."""
        c = self.cfg_caza
        if not c.activar or not rival_paso_envido(obs):
            return False
        n = self.memoria.intentos_pesca(self.rival_id)
        f = self.memoria.estimar_pesca(self.rival_id, c)
        confirmado_no_pescador = n >= c.n0_confianza and f <= c.f_base
        umbral = c.value_cant_explota if confirmado_no_pescador else c.value_cant_default
        return obs.mi_tanto >= umbral

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
