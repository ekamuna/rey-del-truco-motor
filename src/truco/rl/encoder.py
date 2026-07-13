"""Encoder: convierte el estado observable en un vector de números para la red,
y define el espacio de acciones completo (jugar cualquier carta + cantos).

A diferencia del Q tabular, acá NO agrupamos a mano: le damos el estado crudo y
la red arma sus propias features. Y la red **también elige la carta** (una acción
por cada carta posible), sin heurística fija.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from truco.core.acciones import Accion, TipoAccion
from truco.core.cards import NUMEROS, Carta, Palo
from truco.core.state import EstadoObservable

# --- Espacio de cartas y de acciones -----------------------------------------

#: Las 40 cartas en orden canónico; su índice identifica la acción "jugar esa carta".
CARTAS: list[Carta] = [Carta(n, p) for p in Palo for n in NUMEROS]
_INDICE_CARTA: dict[Carta, int] = {c: i for i, c in enumerate(CARTAS)}

#: Cantos/respuestas, en orden fijo. Sus índices van después de las 40 cartas.
CANTOS_ORDEN: tuple[TipoAccion, ...] = (
    TipoAccion.ENVIDO,
    TipoAccion.REAL_ENVIDO,
    TipoAccion.FALTA_ENVIDO,
    TipoAccion.TRUCO,
    TipoAccion.RETRUCO,
    TipoAccion.VALE_CUATRO,
    TipoAccion.QUIERO,
    TipoAccion.NO_QUIERO,
    TipoAccion.MAZO,
)
_INDICE_CANTO: dict[TipoAccion, int] = {t: 40 + i for i, t in enumerate(CANTOS_ORDEN)}

#: Tamaño del espacio de acciones (40 cartas + 9 cantos).
N_ACCIONES = 40 + len(CANTOS_ORDEN)


def indice_de_accion(accion: Accion) -> int:
    if accion.tipo is TipoAccion.JUGAR:
        assert accion.carta is not None
        return _INDICE_CARTA[accion.carta]
    return _INDICE_CANTO[accion.tipo]


def mascara_legal(concretas: tuple[Accion, ...]) -> NDArray[np.bool_]:
    """Vector booleano (N_ACCIONES,): True en las acciones legales ahora."""
    mascara = np.zeros(N_ACCIONES, dtype=np.bool_)
    for accion in concretas:
        mascara[indice_de_accion(accion)] = True
    return mascara


def accion_desde_indice(indice: int, concretas: tuple[Accion, ...]) -> Accion:
    """Traduce el índice elegido por la red a la acción concreta legal."""
    for accion in concretas:
        if indice_de_accion(accion) == indice:
            return accion
    return concretas[0]  # red de seguridad (no debería pasar con la máscara)


# --- Codificación del estado -------------------------------------------------


def _multi_hot(cartas: tuple[Carta, ...]) -> NDArray[np.float32]:
    v = np.zeros(40, dtype=np.float32)
    for c in cartas:
        v[_INDICE_CARTA[c]] = 1.0
    return v


def _carta_hot(carta: Carta | None) -> NDArray[np.float32]:
    v = np.zeros(40, dtype=np.float32)
    if carta is not None:
        v[_INDICE_CARTA[carta]] = 1.0
    return v


def codificar(obs: EstadoObservable) -> NDArray[np.float32]:
    """Estado observable → vector de floats (features crudas para la red)."""
    jugador, rival = obs.jugador, 1 - obs.jugador

    partes: list[NDArray[np.float32]] = [
        _multi_hot(obs.mi_mano),  # 40: mis cartas
        _carta_hot(obs.mesa[jugador]),  # 40: mi carta en la mesa
        _carta_hot(obs.mesa[rival]),  # 40: la del rival en la mesa
    ]

    # 9: resultado de cada baza (yo / rival / parda), 3 bazas
    bazas = np.zeros((3, 3), dtype=np.float32)
    for i, b in enumerate(obs.bazas[:3]):
        if b.ganador is None:
            bazas[i, 2] = 1.0
        elif b.ganador == jugador:
            bazas[i, 0] = 1.0
        else:
            bazas[i, 1] = 1.0
    partes.append(bazas.reshape(-1))

    # 3: categoría del canto pendiente (ninguno / envido / truco)
    pend = np.zeros(3, dtype=np.float32)
    if obs.pendiente is None:
        pend[0] = 1.0
    elif obs.pendiente.categoria == "envido":
        pend[1] = 1.0
    else:
        pend[2] = 1.0
    partes.append(pend)

    # 4: nivel de truco (one-hot 0..3)
    nivel = np.zeros(4, dtype=np.float32)
    nivel[min(obs.nivel_truco, 3)] = 1.0
    partes.append(nivel)

    # varios escalares
    objetivo = max(obs.objetivo, 1)
    escalares = np.array(
        [
            1.0 if obs.truco_querido else 0.0,
            1.0 if obs.envido_resuelto else 0.0,
            obs.mi_tanto / 33.0,
            obs.puntos_partida[jugador] / objetivo,
            obs.puntos_partida[rival] / objetivo,
            obs.objetivo / 30.0,
            1.0 if obs.soy_mano else 0.0,
            obs.cartas_rival / 3.0,
        ],
        dtype=np.float32,
    )
    partes.append(escalares)

    return np.concatenate(partes)


#: Dimensión del vector de entrada (se calcula una vez con un estado dummy).
def _calcular_dim() -> int:
    from truco.core.engine import iniciar, observacion_de

    estado = iniciar(
        (CARTAS[0], CARTAS[1], CARTAS[2]),
        (CARTAS[3], CARTAS[4], CARTAS[5]),
    )
    return int(codificar(observacion_de(estado, 0)).shape[0])


DIM = _calcular_dim()
