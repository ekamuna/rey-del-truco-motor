"""Motor de la ronda: máquina de estados con cartas, envido, truco y mazo.

Referencia: ``docs/REGLAMENTO.md`` §3-§8.

Funciones puras sobre :class:`EstadoRonda`: ``aplicar`` no muta, devuelve un
estado nuevo. La negociación (cantos y respuestas) se modela con una única
:class:`Negociacion` activa, más un hueco ``truco_suspendido`` para el caso de
"el envido está primero".
"""

from __future__ import annotations

from dataclasses import replace

from truco.core.acciones import (
    CANTOS_ENVIDO,
    CANTOS_TRUCO,
    CATEGORIA_ENVIDO,
    CATEGORIA_TRUCO,
    Accion,
    TipoAccion,
    canto,
    jugar_carta,
)
from truco.core.cards import Carta, fuerza_truco
from truco.core.mazo import repartir
from truco.core.scoring import (
    NIVEL_TRUCO,
    NO_QUIERO_TRUCO,
    tanto_envido,
    valor_envido_no_querido,
    valor_envido_querido,
    valor_falta_envido,
)
from truco.core.state import (
    EstadoObservable,
    EstadoRonda,
    Negociacion,
    ResultadoBaza,
)

#: Valor del truco según el nivel querido (0 = sin cantar → vale 1).
_VALOR_TRUCO_POR_NIVEL = {0: 1, 1: 2, 2: 3, 3: 4}


# --- Construcción ------------------------------------------------------------


def iniciar(
    mano0: tuple[Carta, ...],
    mano1: tuple[Carta, ...],
    mano: int = 0,
    puntos_partida: tuple[int, int] = (0, 0),
    objetivo: int = 15,
) -> EstadoRonda:
    """Crea una ronda a partir de dos manos ya repartidas."""
    m0, m1 = tuple(mano0), tuple(mano1)
    return EstadoRonda(
        puntos_partida=puntos_partida,
        objetivo=objetivo,
        manos=(m0, m1),
        mano=mano,
        turno=mano,
        mesa=(None, None),
        bazas=(),
        tantos=(tanto_envido(m0), tanto_envido(m1)),
    )


def nueva_ronda(
    seed: int | None = None,
    mano: int = 0,
    puntos_partida: tuple[int, int] = (0, 0),
    objetivo: int = 15,
) -> EstadoRonda:
    """Reparte (reproducible por ``seed``) e inicia una ronda."""
    mano0, mano1 = repartir(seed)
    return iniciar(mano0, mano1, mano=mano, puntos_partida=puntos_partida, objetivo=objetivo)


# --- Consultas ---------------------------------------------------------------


def actor(estado: EstadoRonda) -> int:
    """Quién debe actuar: el que responde si hay canto pendiente, si no el de turno."""
    if estado.pendiente is not None:
        return estado.pendiente.a_responder
    return estado.turno


def observacion_de(estado: EstadoRonda, jugador: int) -> EstadoObservable:
    """Proyecta el estado completo a lo que ``jugador`` puede ver."""
    rival = 1 - jugador
    return EstadoObservable(
        jugador=jugador,
        mi_mano=estado.manos[jugador],
        mano=estado.mano,
        turno=estado.turno,
        mesa=estado.mesa,
        bazas=estado.bazas,
        cartas_rival=len(estado.manos[rival]),
        pendiente=estado.pendiente,
        nivel_truco=estado.nivel_truco,
        truco_querido=estado.truco_querido,
        envido_resuelto=estado.envido_resuelto,
        puntos_partida=estado.puntos_partida,
        objetivo=estado.objetivo,
        terminada=estado.terminada,
        ganador=estado.ganador,
        puntos_ronda=estado.puntos_ronda,
        mi_tanto=estado.tantos[jugador],
        tanto_rival=_tanto_rival_publico(estado, rival),
        envido_rival=_senal_envido_rival(estado, jugador),
    )


def _senal_envido_rival(estado: EstadoRonda, jugador: int) -> str:
    """Qué reveló el rival con su acción de envido esta ronda (canal de información, FIX G).
    No expone tantos ocultos: sólo la CATEGORÍA de la jugada, que el PIMC traduce en una
    poda por tanto de las manos que le imagina al rival.
      - "rival_canto"    : el rival cantó y NO hubo showdown (yo no quise) → tanto ALTO.
      - "rival_no_quiso" : yo canté y el rival no quiso → su tanto es BAJO.
      - "nadie_canto"    : el envido se cerró sin que nadie cantara → sin declaración.
      - "sin_info"       : no resuelto, o resuelto con quiero (ahí manda ``tanto_rival``)."""
    rival = 1 - jugador
    if not estado.envido_resuelto or estado.envido_con_quiero:
        return "sin_info"
    if estado.envido_ganador == rival:  # el rival cantó y yo no quise
        return "rival_canto"
    if estado.envido_ganador == jugador:  # yo canté y el rival no quiso
        return "rival_no_quiso"
    return "nadie_canto"  # envido_ganador is None → nadie cantó


def tanto_rival_publico(estado: EstadoRonda, rival: int) -> int | None:
    """Alias público del filtro de fidelidad: el tanto del rival sólo si es información
    que apareció en la mesa (envido con quiero y el rival mostró). Lo usa la caza de
    faroles para no inventar una regla de visibilidad distinta a la del motor."""
    return _tanto_rival_publico(estado, rival)


def _tanto_rival_publico(estado: EstadoRonda, rival: int) -> int | None:
    """El tanto del rival es público si cantó el número: es mano (canta primero)
    o ganó el envido (canta para superar). Si perdió siendo pie dijo 'son buenas'."""
    if not estado.envido_con_quiero:
        return None
    if estado.mano == rival or estado.envido_ganador == rival:
        return estado.tantos[rival]
    return None


def acciones_legales(estado: EstadoRonda) -> tuple[Accion, ...]:
    """Acciones que el actor de turno puede tomar."""
    if estado.terminada:
        return ()
    quien = actor(estado)
    if estado.pendiente is not None:
        return _acciones_respuesta(estado, quien)

    acciones = [jugar_carta(c) for c in estado.manos[quien]]
    acciones += [canto(t) for t in _cantos_truco_disponibles(estado, quien)]
    if _envido_disponible(estado, quien):
        acciones += [canto(t) for t in CANTOS_ENVIDO]
    acciones.append(canto(TipoAccion.MAZO))
    return tuple(acciones)


def _acciones_respuesta(estado: EstadoRonda, quien: int) -> tuple[Accion, ...]:
    neg = estado.pendiente
    assert neg is not None
    acciones = [canto(TipoAccion.QUIERO), canto(TipoAccion.NO_QUIERO)]
    acciones += [canto(t) for t in _subidas(neg)]
    # "El envido está primero": ante un truco pendiente, en la primera baza,
    # el que debe responder puede cantar envido en lugar de contestar.
    if neg.categoria == CATEGORIA_TRUCO and _envido_disponible(estado, quien):
        acciones += [canto(t) for t in CANTOS_ENVIDO]
    return tuple(acciones)


def _envido_disponible(estado: EstadoRonda, jugador: int) -> bool:
    """El envido se puede cantar en la primera baza, antes de que ``jugador``
    haya jugado su carta y sin que el truco esté querido."""
    return (
        not estado.envido_resuelto
        and not estado.truco_querido
        and len(estado.bazas) == 0
        and estado.mesa[jugador] is None
    )


def _cantos_truco_disponibles(estado: EstadoRonda, quien: int) -> list[TipoAccion]:
    if estado.nivel_truco == 0:
        return [TipoAccion.TRUCO]
    if estado.truco_querido and estado.nivel_truco < 3 and estado.puede_subir_truco == quien:
        return [CANTOS_TRUCO[estado.nivel_truco]]  # índice = nivel actual → siguiente canto
    return []


def _subidas(neg: Negociacion) -> list[TipoAccion]:
    if neg.categoria == CATEGORIA_ENVIDO:
        return _subidas_envido(neg.cantos)
    return _subidas_truco(neg.ultimo)


def _subidas_envido(cantos: tuple[TipoAccion, ...]) -> list[TipoAccion]:
    ultimo = cantos[-1]
    if ultimo is TipoAccion.ENVIDO:
        res = [TipoAccion.REAL_ENVIDO, TipoAccion.FALTA_ENVIDO]
        if cantos.count(TipoAccion.ENVIDO) < 2:
            res.insert(0, TipoAccion.ENVIDO)  # envido-envido
        return res
    if ultimo is TipoAccion.REAL_ENVIDO:
        return [TipoAccion.FALTA_ENVIDO]
    return []  # falta envido: no se sube más


def _subidas_truco(ultimo: TipoAccion) -> list[TipoAccion]:
    idx = CANTOS_TRUCO.index(ultimo)
    return [CANTOS_TRUCO[idx + 1]] if idx + 1 < len(CANTOS_TRUCO) else []


# --- Transición --------------------------------------------------------------


def aplicar(estado: EstadoRonda, accion: Accion) -> EstadoRonda:
    """Aplica una acción legal y devuelve el nuevo estado."""
    if estado.terminada:
        raise RuntimeError("La ronda ya terminó.")
    if accion not in acciones_legales(estado):
        raise ValueError(f"Acción ilegal: {accion}")

    quien = actor(estado)
    tipo = accion.tipo
    if tipo is TipoAccion.JUGAR:
        assert accion.carta is not None
        return _jugar_carta(estado, accion.carta, quien)
    if tipo in CANTOS_ENVIDO:
        return _cantar_envido(estado, tipo, quien)
    if tipo in CANTOS_TRUCO:
        return _cantar_truco(estado, tipo, quien)
    if tipo is TipoAccion.QUIERO:
        return _responder_quiero(estado, quien)
    if tipo is TipoAccion.NO_QUIERO:
        return _responder_no_quiero(estado, quien)
    return _irse_al_mazo(estado, quien)


def _jugar_carta(estado: EstadoRonda, carta: Carta, quien: int) -> EstadoRonda:
    manos = list(estado.manos)
    manos[quien] = tuple(c for c in manos[quien] if c != carta)
    mesa: list[Carta | None] = list(estado.mesa)
    mesa[quien] = carta

    rival = 1 - quien
    if mesa[rival] is None:
        return replace(estado, manos=(manos[0], manos[1]), mesa=(mesa[0], mesa[1]), turno=rival)

    c0, c1 = mesa[0], mesa[1]
    assert c0 is not None and c1 is not None
    ganador_baza = _ganador_baza(c0, c1)
    bazas = estado.bazas + (ResultadoBaza(cartas=(c0, c1), ganador=ganador_baza),)

    ganador_ronda = _resolver_ronda(bazas, estado.mano)
    if ganador_ronda is not None:
        valor = _VALOR_TRUCO_POR_NIVEL[estado.nivel_truco]
        return replace(
            estado,
            manos=(manos[0], manos[1]),
            mesa=(None, None),
            bazas=bazas,
            puntos_ronda=_sumar(estado.puntos_ronda, ganador_ronda, valor),
            terminada=True,
            ganador=ganador_ronda,
            motivo="bazas",
            turno=ganador_ronda,
        )

    siguiente = estado.mano if ganador_baza is None else ganador_baza
    return replace(
        estado, manos=(manos[0], manos[1]), mesa=(None, None), bazas=bazas, turno=siguiente
    )


def _cantar_envido(estado: EstadoRonda, tipo: TipoAccion, quien: int) -> EstadoRonda:
    neg = estado.pendiente
    nueva = Negociacion(
        categoria=CATEGORIA_ENVIDO,
        cantos=(neg.cantos + (tipo,)) if (neg and neg.categoria == CATEGORIA_ENVIDO) else (tipo,),
        a_responder=1 - quien,
    )
    if neg is not None and neg.categoria == CATEGORIA_TRUCO:
        # Envido está primero: suspender el truco pendiente.
        return replace(estado, pendiente=nueva, truco_suspendido=neg)
    return replace(estado, pendiente=nueva)


def _cantar_truco(estado: EstadoRonda, tipo: TipoAccion, quien: int) -> EstadoRonda:
    neg = estado.pendiente
    cantos = (neg.cantos + (tipo,)) if neg is not None else (tipo,)
    nueva = Negociacion(categoria=CATEGORIA_TRUCO, cantos=cantos, a_responder=1 - quien)
    return replace(estado, pendiente=nueva)


def _responder_quiero(estado: EstadoRonda, quien: int) -> EstadoRonda:
    neg = estado.pendiente
    assert neg is not None
    if neg.categoria == CATEGORIA_ENVIDO:
        return _resolver_envido_querido(estado, neg)
    nivel = NIVEL_TRUCO[neg.ultimo]
    return replace(
        estado, pendiente=None, nivel_truco=nivel, truco_querido=True, puede_subir_truco=quien
    )


def _responder_no_quiero(estado: EstadoRonda, quien: int) -> EstadoRonda:
    neg = estado.pendiente
    assert neg is not None
    if neg.categoria == CATEGORIA_ENVIDO:
        valor = valor_envido_no_querido(neg.cantos)
        estado2 = replace(
            estado,
            pendiente=None,
            envido_resuelto=True,
            envido_ganador=neg.cantor,
            puntos_envido=valor,
            puntos_ronda=_sumar(estado.puntos_ronda, neg.cantor, valor),
        )
        return _restaurar_truco(estado2)

    valor = NO_QUIERO_TRUCO[neg.ultimo]
    return replace(
        estado,
        pendiente=None,
        puntos_ronda=_sumar(estado.puntos_ronda, neg.cantor, valor),
        terminada=True,
        ganador=neg.cantor,
        motivo="no_quiero_truco",
    )


def _irse_al_mazo(estado: EstadoRonda, quien: int) -> EstadoRonda:
    rival = 1 - quien
    valor = _VALOR_TRUCO_POR_NIVEL[estado.nivel_truco]
    return replace(
        estado,
        puntos_ronda=_sumar(estado.puntos_ronda, rival, valor),
        terminada=True,
        ganador=rival,
        motivo="mazo",
    )


def _resolver_envido_querido(estado: EstadoRonda, neg: Negociacion) -> EstadoRonda:
    valor_falta = valor_falta_envido(estado.puntos_partida, estado.objetivo)
    valor = valor_envido_querido(neg.cantos, valor_falta)
    t0, t1 = estado.tantos
    if t0 > t1:
        ganador = 0
    elif t1 > t0:
        ganador = 1
    else:
        ganador = estado.mano  # empate de tanto → gana el mano
    estado2 = replace(
        estado,
        pendiente=None,
        envido_resuelto=True,
        envido_con_quiero=True,
        envido_ganador=ganador,
        puntos_envido=valor,
        puntos_ronda=_sumar(estado.puntos_ronda, ganador, valor),
    )
    return _restaurar_truco(estado2)


def _restaurar_truco(estado: EstadoRonda) -> EstadoRonda:
    if estado.truco_suspendido is not None:
        return replace(estado, pendiente=estado.truco_suspendido, truco_suspendido=None)
    return estado


# --- Auxiliares --------------------------------------------------------------


def _sumar(puntos: tuple[int, int], jugador: int, cantidad: int) -> tuple[int, int]:
    if jugador == 0:
        return (puntos[0] + cantidad, puntos[1])
    return (puntos[0], puntos[1] + cantidad)


def _ganador_baza(c0: Carta, c1: Carta) -> int | None:
    f0, f1 = fuerza_truco(c0), fuerza_truco(c1)
    if f0 > f1:
        return 0
    if f1 > f0:
        return 1
    return None


def _resolver_ronda(bazas: tuple[ResultadoBaza, ...], mano: int) -> int | None:
    """Ganador de la ronda por las bazas, o None si aún no se define (§3)."""
    ganadores = [b.ganador for b in bazas]
    if len(ganadores) < 2:
        return None

    a, b = ganadores[0], ganadores[1]
    if a is not None and a == b:
        return a  # 2-0
    if a is not None and b is None:
        return a  # gana la 1ª, emparda la 2ª
    if a is None and b is not None:
        return b  # emparda la 1ª, gana la 2ª

    if len(ganadores) < 3:
        return None

    c = ganadores[2]
    if a is not None and b is not None:
        return c if c is not None else a  # 1-1: la 3ª; si es parda, gana quien ganó la 1ª
    return c if c is not None else mano  # dos pardas: la 3ª; si es parda, gana el mano
