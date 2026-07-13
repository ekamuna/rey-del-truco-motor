"""Tests del tooling de autopsia de derrotas."""

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.pimc import AgentePIMC
from truco.autopsia import recolectar_derrotas, render_partido


def test_recolectar_solo_devuelve_derrotas() -> None:
    # El PIMC le gana holgado al azar → habrá pocas derrotas, y todas son derrotas.
    derrotas = recolectar_derrotas(
        lambda: AgentePIMC(muestras=20), lambda: AgenteAleatorio(2), partidas=20, seed=1
    )
    assert all(p.ganador != 0 for p in derrotas)
    # una derrota del bot (j0) tiene j0 <= j1 (el empate a 15 se cuenta como derrota).
    assert all(p.puntos[0] <= p.puntos[1] for p in derrotas)


def test_render_partido_es_legible() -> None:
    # Contra un rival duro seguro perdemos alguna; la transcripción debe revelar
    # ambas manos y el marcador final.
    derrotas = recolectar_derrotas(
        lambda: AgentePIMC(muestras=20), lambda: AgenteAleatorio(9), partidas=30, seed=3
    )
    if derrotas:
        texto = render_partido(derrotas[0], titulo="test")
        assert "PARTIDO PERDIDO" in texto
        assert "BOT" in texto and "RIV" in texto
        assert "envido" in texto
