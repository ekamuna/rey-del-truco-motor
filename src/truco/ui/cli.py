"""CLI: jugá una ronda humano (jugador 0) contra la máquina (jugador 1).

Ejecutar con::

    uv run truco
    # o
    uv run python -m truco.ui.cli

Por ahora la máquina juega al azar (M3) y no hay envido ni truco cantados
(eso llega en M4/M5). Es una ronda suelta, para probar el flujo.
"""

from __future__ import annotations

from truco.agents.aleatorio import AgenteAleatorio
from truco.core.cards import Carta
from truco.core.engine import nueva_ronda
from truco.core.state import EstadoRonda
from truco.game_loop import jugar_ronda
from truco.ui.humano import AgenteHumano
from truco.ui.render import formato_baza, formato_jugada


def _mostrar_jugada(estado: EstadoRonda, jugador: int, carta: Carta) -> None:
    print(formato_jugada(jugador, carta))
    # Si la baza se cerró (la mesa quedó vacía), mostrar su resultado.
    if estado.mesa == (None, None) and estado.bazas:
        print(formato_baza(estado.bazas[-1]))


def main(seed: int | None = None) -> None:
    humano = AgenteHumano()
    maquina = AgenteAleatorio(seed=seed)
    estado = nueva_ronda(seed=seed, mano=0)

    print("=== Rey del Truco — ronda de prueba ===")
    estado = jugar_ronda(estado, (humano, maquina), al_jugar=_mostrar_jugada)

    print()
    if estado.ganador == 0:
        print("🏆 ¡Ganaste la ronda!")
    else:
        print("🤖 Ganó la máquina.")


if __name__ == "__main__":
    main()
