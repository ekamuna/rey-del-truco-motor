"""CLI: jugá una PARTIDA completa (humano vs bot de reglas).

Ejecutar con::

    uv run truco
    # o
    uv run python -m truco.ui.cli

Ya con envido, truco y marcador de partida (M4/M5). El humano es el jugador 0.
"""

from __future__ import annotations

import random

from truco.agents.reglas import AgenteReglas
from truco.core.acciones import Accion, TipoAccion
from truco.core.engine import nueva_ronda
from truco.core.state import EstadoRonda
from truco.game_loop import jugar_ronda
from truco.ui.humano import AgenteHumano
from truco.ui.render import formato_accion, formato_baza

OBJETIVO = 15


def _mostrar(estado: EstadoRonda, jugador: int, accion: Accion) -> None:
    print(formato_accion(jugador, accion))
    if accion.tipo is TipoAccion.JUGAR and estado.mesa == (None, None) and estado.bazas:
        print(formato_baza(estado.bazas[-1]))


def main(seed: int | None = None) -> None:
    humano = AgenteHumano()
    maquina = AgenteReglas()
    rng = random.Random(seed)
    puntos = (0, 0)
    mano = 0

    print(f"=== Rey del Truco — partida a {OBJETIVO} (vos sos el jugador 0) ===")
    while max(puntos) < OBJETIVO:
        estado = nueva_ronda(
            seed=rng.randrange(2**31), mano=mano, puntos_partida=puntos, objetivo=OBJETIVO
        )
        print(f"\n--- Nueva ronda (mano: jugador {mano}) ---")
        estado = jugar_ronda(estado, (humano, maquina), al_actuar=_mostrar)
        puntos = (puntos[0] + estado.puntos_ronda[0], puntos[1] + estado.puntos_ronda[1])
        print(
            f"Puntos de la ronda: vos +{estado.puntos_ronda[0]}, máquina +{estado.puntos_ronda[1]}"
        )
        print(f"Marcador: vos {puntos[0]} - {puntos[1]} máquina")
        mano = 1 - mano

    print("\n" + ("🏆 ¡Ganaste la partida!" if puntos[0] > puntos[1] else "🤖 Ganó la máquina."))


if __name__ == "__main__":
    main()
