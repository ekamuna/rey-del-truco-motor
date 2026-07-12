"""CLI: jugá una PARTIDA completa (humano vs bot de reglas).

Ejecutar con::

    uv run truco
    # o
    uv run python -m truco.ui.cli

Ya con envido, truco y marcador de partida (M4/M5). El humano es el jugador 0.
La presentación (tablero, narración de jugadas, resúmenes) vive en
:mod:`truco.ui.narrador`.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from truco.agents.reglas import AgenteReglas
from truco.core.acciones import Accion
from truco.core.engine import nueva_ronda
from truco.core.state import EstadoRonda
from truco.game_loop import jugar_ronda
from truco.ui.humano import AgenteHumano
from truco.ui.narrador import (
    encabezado_ronda,
    narrar_evento,
    resumen_partida,
    resumen_ronda,
)

OBJETIVO = 15


def main(seed: int | None = None, escribir: Callable[[str], None] = print) -> None:
    humano = AgenteHumano()
    maquina = AgenteReglas()
    rng = random.Random(seed)
    puntos = (0, 0)
    mano = 0
    numero = 0

    def narrar(antes: EstadoRonda, quien: int, accion: Accion, despues: EstadoRonda) -> None:
        for linea in narrar_evento(antes, quien, accion, despues):
            escribir(linea)

    escribir(f"═══ Rey del Truco — partida a {OBJETIVO} (vos sos el jugador 0) ═══")
    while max(puntos) < OBJETIVO:
        numero += 1
        escribir(encabezado_ronda(numero, mano))
        estado = nueva_ronda(
            seed=rng.randrange(2**31), mano=mano, puntos_partida=puntos, objetivo=OBJETIVO
        )
        estado = jugar_ronda(estado, (humano, maquina), al_actuar=narrar)
        for linea in resumen_ronda(estado):
            escribir(linea)
        puntos = (puntos[0] + estado.puntos_ronda[0], puntos[1] + estado.puntos_ronda[1])
        escribir(f"  Marcador de la partida:  vos {puntos[0]}  —  {puntos[1]} la máquina")
        mano = 1 - mano

    escribir(resumen_partida(puntos, OBJETIVO))


if __name__ == "__main__":
    main()
