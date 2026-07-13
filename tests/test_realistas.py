"""Tests de los rivales realistas del panel (T4): que juegan legal y son diversos."""

from truco.agents.pimc import AgentePIMC
from truco.agents.realistas import (
    AgenteEstratega,
    AgenteMentiroso,
    agresivo_real,
    conservador_real,
    estratega_real,
    mentiroso_real,
)
from truco.partida import jugar_partida

_FACTORIES = [conservador_real, agresivo_real, mentiroso_real, estratega_real]


def test_realistas_juegan_partidas_legales() -> None:
    # Cada realista completa partidos enteros contra el PIMC sin acciones ilegales.
    for fab in _FACTORIES:
        for seed in range(6):
            r = jugar_partida((fab(1), AgentePIMC(muestras=15)), seed=seed, mano_inicial=seed % 2)
            assert r.ganador in (0, 1)
            assert max(r.puntos) >= 15


def test_mentiroso_es_condicional_no_al_voleo() -> None:
    # El mentiroso realista NO usa frecuencia_farol (RNG): su farol es condicional.
    m = mentiroso_real(1)
    assert isinstance(m, AgenteMentiroso)
    assert m.cfg.frecuencia_farol == 0.0


def test_estratega_hace_slow_play() -> None:
    e = estratega_real(1)
    assert isinstance(e, AgenteEstratega)
    assert e.cfg.frecuencia_farol == 0.0
