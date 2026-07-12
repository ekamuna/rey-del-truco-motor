"""Tests de la partida completa y el harness de evaluación (M5)."""

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.reglas import AgenteReglas
from truco.evaluacion import enfrentar
from truco.partida import jugar_partida


def test_partida_termina_con_un_ganador() -> None:
    r = jugar_partida((AgenteReglas(), AgenteAleatorio(1)), objetivo=15, seed=1)
    assert r.ganador in (0, 1)
    assert max(r.puntos) >= 15
    assert r.rondas >= 1


def test_partida_es_reproducible() -> None:
    a = jugar_partida((AgenteReglas(), AgenteReglas()), objetivo=15, seed=123)
    b = jugar_partida((AgenteReglas(), AgenteReglas()), objetivo=15, seed=123)
    assert a == b


def test_enfrentar_cuenta_todas_las_partidas() -> None:
    res = enfrentar(
        lambda: AgenteAleatorio(0), lambda: AgenteAleatorio(1), partidas=10, objetivo=15, seed=4
    )
    assert res.partidas == 10
    assert res.victorias_a + res.victorias_b == 10


def test_reglas_le_gana_holgado_al_aleatorio() -> None:
    res = enfrentar(
        lambda: AgenteReglas(),
        lambda: AgenteAleatorio(seed=0),
        partidas=40,
        objetivo=15,
        seed=2024,
    )
    assert res.winrate_a > 0.7, f"winrate del bot de reglas: {res.winrate_a:.0%}"
