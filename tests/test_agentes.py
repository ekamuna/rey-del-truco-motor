"""Tests de los agentes y el bucle de juego (M3)."""

import pytest

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.base import Accion, Agent
from truco.core.cards import Carta, Palo
from truco.core.engine import iniciar, nueva_ronda
from truco.core.state import EstadoObservable
from truco.game_loop import jugar_ronda
from truco.ui.humano import AgenteHumano

MACHO = Carta(1, Palo.ESPADA)
BASTO = Carta(1, Palo.BASTO)
CUATRO_ORO = Carta(4, Palo.ORO)
CUATRO_ESP = Carta(4, Palo.ESPADA)
CINCO_ESP = Carta(5, Palo.ESPADA)
CINCO_ORO = Carta(5, Palo.ORO)


# --- AgenteAleatorio ---------------------------------------------------------


def test_aleatorio_elige_una_carta_legal() -> None:
    agente = AgenteAleatorio(seed=1)
    obs = EstadoObservable(
        jugador=0,
        mi_mano=(MACHO, CUATRO_ORO),
        mano=0,
        turno=0,
        mesa=(None, None),
        bazas=(),
        cartas_rival=2,
        terminada=False,
        ganador=None,
    )
    acciones = (MACHO, CUATRO_ORO)
    assert agente.actuar(obs, acciones) in acciones


def test_aleatorio_es_reproducible_por_seed() -> None:
    r1 = nueva_ronda(seed=3)
    r2 = nueva_ronda(seed=3)
    a, b = AgenteAleatorio(seed=99), AgenteAleatorio(seed=99)
    from truco.core.engine import acciones_legales

    assert a.actuar(None, acciones_legales(r1)) == b.actuar(None, acciones_legales(r2))  # type: ignore[arg-type]


# --- AgenteHumano (IO inyectada) ---------------------------------------------


def test_humano_elige_por_indice() -> None:
    entradas = iter(["1"])
    salidas: list[str] = []
    humano = AgenteHumano(leer=lambda _: next(entradas), escribir=salidas.append)
    obs = EstadoObservable(
        jugador=0,
        mi_mano=(MACHO, CUATRO_ORO, CINCO_ESP),
        mano=0,
        turno=0,
        mesa=(None, None),
        bazas=(),
        cartas_rival=3,
        terminada=False,
        ganador=None,
    )
    acciones = (MACHO, CUATRO_ORO, CINCO_ESP)
    assert humano.actuar(obs, acciones) == CUATRO_ORO  # índice 1
    assert any("Tus cartas" in s for s in salidas)  # mostró el estado


def test_humano_reintenta_con_entrada_invalida() -> None:
    entradas = iter(["x", "9", "0"])  # no-número, fuera de rango, válida
    salidas: list[str] = []
    humano = AgenteHumano(leer=lambda _: next(entradas), escribir=salidas.append)
    obs = EstadoObservable(
        jugador=0,
        mi_mano=(MACHO, CUATRO_ORO),
        mano=0,
        turno=0,
        mesa=(None, None),
        bazas=(),
        cartas_rival=2,
        terminada=False,
        ganador=None,
    )
    assert humano.actuar(obs, (MACHO, CUATRO_ORO)) == MACHO
    assert any("inválida" in s for s in salidas)
    assert any("rango" in s for s in salidas)


# --- game_loop ---------------------------------------------------------------


def test_jugar_ronda_completa_con_dos_aleatorios() -> None:
    estado = nueva_ronda(seed=5, mano=0)
    final = jugar_ronda(estado, (AgenteAleatorio(1), AgenteAleatorio(2)))
    assert final.terminada
    assert final.ganador in (0, 1)
    assert len(final.bazas) >= 2  # una ronda dura entre 2 y 3 bazas


def test_game_loop_registra_las_jugadas_en_el_callback() -> None:
    estado = nueva_ronda(seed=5, mano=0)
    jugadas: list[tuple[int, Carta]] = []
    jugar_ronda(
        estado,
        (AgenteAleatorio(1), AgenteAleatorio(2)),
        al_jugar=lambda _e, j, c: jugadas.append((j, c)),
    )
    assert len(jugadas) >= 4  # al menos 2 bazas × 2 jugadas


def test_game_loop_rechaza_accion_ilegal() -> None:
    class AgenteTramposo(Agent):
        def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
            return BASTO  # nunca está en su mano

    estado = iniciar((MACHO, CUATRO_ORO, CINCO_ESP), (CUATRO_ESP, BASTO, CINCO_ORO), mano=0)
    with pytest.raises(ValueError, match="ilegal"):
        jugar_ronda(estado, (AgenteTramposo(), AgenteAleatorio(1)))
