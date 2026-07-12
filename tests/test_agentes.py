"""Tests de los agentes y el bucle de juego (M3/M4)."""

import pytest

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.base import Agent
from truco.core.acciones import Accion, jugar_carta
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, iniciar, nueva_ronda, observacion_de
from truco.core.state import EstadoObservable
from truco.game_loop import jugar_ronda
from truco.ui.humano import AgenteHumano

MACHO = Carta(1, Palo.ESPADA)
BASTO = Carta(1, Palo.BASTO)
M0 = (MACHO, Carta(4, Palo.ORO), Carta(5, Palo.ESPADA))
M1 = (BASTO, Carta(4, Palo.ESPADA), Carta(5, Palo.ORO))


def _obs_inicial(jugador: int = 0) -> tuple[EstadoObservable, tuple[Accion, ...]]:
    estado = iniciar(M0, M1, mano=0)
    return observacion_de(estado, jugador), acciones_legales(estado)


# --- AgenteAleatorio ---------------------------------------------------------


def test_aleatorio_elige_una_accion_legal() -> None:
    obs, acciones = _obs_inicial()
    assert AgenteAleatorio(seed=1).actuar(obs, acciones) in acciones


def test_aleatorio_es_reproducible_por_seed() -> None:
    obs, acciones = _obs_inicial()
    a, b = AgenteAleatorio(seed=99), AgenteAleatorio(seed=99)
    assert a.actuar(obs, acciones) == b.actuar(obs, acciones)


# --- AgenteHumano (IO inyectada) ---------------------------------------------


def test_humano_elige_por_indice() -> None:
    obs, acciones = _obs_inicial()
    salidas: list[str] = []
    humano = AgenteHumano(leer=lambda _: "0", escribir=salidas.append)
    assert humano.actuar(obs, acciones) == acciones[0]
    assert any("Tus cartas" in s for s in salidas)


def test_humano_reintenta_con_entrada_invalida() -> None:
    obs, acciones = _obs_inicial()
    entradas = iter(["x", "999", "0"])
    salidas: list[str] = []
    humano = AgenteHumano(leer=lambda _: next(entradas), escribir=salidas.append)
    assert humano.actuar(obs, acciones) == acciones[0]
    assert any("inválida" in s for s in salidas)
    assert any("rango" in s for s in salidas)


# --- game_loop ---------------------------------------------------------------


def test_jugar_ronda_completa_con_dos_aleatorios() -> None:
    final = jugar_ronda(nueva_ronda(seed=5, mano=0), (AgenteAleatorio(1), AgenteAleatorio(2)))
    assert final.terminada
    assert final.ganador in (0, 1)


def test_game_loop_rechaza_accion_ilegal() -> None:
    class Tramposo(Agent):
        def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
            return jugar_carta(BASTO)  # nunca está en la mano de j0

    estado = iniciar(M0, M1, mano=0)
    with pytest.raises(ValueError, match="ilegal"):
        jugar_ronda(estado, (Tramposo(), AgenteAleatorio(1)))


def test_muchas_rondas_aleatorias_no_rompen_el_motor() -> None:
    # Robustez: 200 rondas al azar deben terminar siempre, sin excepciones.
    for s in range(200):
        final = jugar_ronda(nueva_ronda(seed=s), (AgenteAleatorio(s), AgenteAleatorio(s + 1)))
        assert final.terminada
        assert final.puntos_ronda[0] >= 0 and final.puntos_ronda[1] >= 0
