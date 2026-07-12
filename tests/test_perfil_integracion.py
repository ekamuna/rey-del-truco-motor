"""Tests de integración: el bot usa el perfil para ajustar sus decisiones."""

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.reglas import AgenteReglas
from truco.core.acciones import Accion, TipoAccion, canto
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, aplicar, iniciar, nueva_ronda, observacion_de
from truco.core.state import EstadoObservable
from truco.game_loop import jugar_ronda
from truco.perfil import Faceta, PerfilDelRival

# Mano floja para el bot (mejor carta: rey = fuerza 6, por debajo del umbral 8).
FLOJA = (Carta(12, Palo.ORO), Carta(4, Palo.COPA), Carta(5, Palo.BASTO))
RIVAL = (Carta(1, Palo.ESPADA), Carta(2, Palo.ORO), Carta(3, Palo.COPA))


def _situacion_respondiendo_truco() -> tuple[EstadoObservable, tuple[Accion, ...]]:
    # j1 (mano) canta truco; ahora el bot (j0) con mano floja debe responder.
    e = iniciar(FLOJA, RIVAL, mano=1)
    e = aplicar(e, canto(TipoAccion.TRUCO))
    return observacion_de(e, 0), acciones_legales(e)


def test_sin_perfil_no_quiere_el_truco_con_mano_floja() -> None:
    obs, acc = _situacion_respondiendo_truco()
    assert AgenteReglas().actuar(obs, acc).tipo is TipoAccion.NO_QUIERO


def test_con_perfil_de_mentiroso_acepta_el_mismo_truco() -> None:
    perfil = PerfilDelRival("mentiroso")
    perfil.conteos["mentiroso_truco|parejo"] = (9, 10)  # miente el ~70% (con prior)
    obs, acc = _situacion_respondiendo_truco()
    assert AgenteReglas(perfil=perfil).actuar(obs, acc).tipo is TipoAccion.QUIERO


def test_perfil_aprende_jugando_varias_rondas() -> None:
    perfil = PerfilDelRival("rival")
    bot = AgenteReglas(perfil=perfil)  # jugador 0
    for s in range(30):
        jugar_ronda(nueva_ronda(seed=s, mano=s % 2), (bot, AgenteAleatorio(s)))
    # Tras 30 rondas, el bot observó cantos del rival y registró algo.
    total = sum(perfil.intentos_global(f) for f in Faceta)
    assert total > 0


def test_agente_sin_perfil_es_backward_compatible() -> None:
    # Un bot sin perfil ignora observar_ronda sin romperse.
    bot = AgenteReglas()
    final = jugar_ronda(nueva_ronda(seed=1), (bot, AgenteAleatorio(2)))
    assert final.terminada
