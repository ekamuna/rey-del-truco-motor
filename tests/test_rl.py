"""Tests del aprendizaje por refuerzo (M6): abstracción, tabla y entrenamiento."""

from pathlib import Path

from truco.agents.aleatorio import AgenteAleatorio
from truco.core.acciones import TipoAccion, canto
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, aplicar, iniciar, nueva_ronda, observacion_de
from truco.game_loop import jugar_ronda
from truco.rl.agente_q import AgenteQ
from truco.rl.entrenar import entrenar, winrate_vs
from truco.rl.estado import AccionQ, a_concreta, acciones_legales_q, clave_estado
from truco.rl.qtable import QTable

M0 = (Carta(1, Palo.ESPADA), Carta(4, Palo.ORO), Carta(5, Palo.ESPADA))
M1 = (Carta(1, Palo.BASTO), Carta(4, Palo.ESPADA), Carta(5, Palo.ORO))


def test_qtable_guarda_y_carga(tmp_path: Path) -> None:
    tabla = QTable()
    clave = ("libre", 2, 2, 0, 0, True)
    tabla.actualizar(clave, AccionQ.ENVIDO, 1.0, 0.5)
    ruta = tmp_path / "q.json"
    tabla.guardar(ruta)
    assert QTable.cargar(ruta).q == tabla.q


def test_acciones_legales_q_libre_incluye_jugar_y_cantos() -> None:
    e = iniciar(M0, M1, mano=0)
    q = acciones_legales_q(observacion_de(e, 0), acciones_legales(e))
    assert AccionQ.JUGAR in q
    assert AccionQ.ENVIDO in q
    assert AccionQ.TRUCO in q


def test_acciones_legales_q_respondiendo_no_deja_jugar() -> None:
    e = aplicar(iniciar(M0, M1, mano=0), canto(TipoAccion.ENVIDO))  # j0 canta; responde j1
    q = acciones_legales_q(observacion_de(e, 1), acciones_legales(e))
    assert AccionQ.QUIERO in q and AccionQ.NO_QUIERO in q
    assert AccionQ.JUGAR not in q


def test_a_concreta_traduce_a_accion_legal() -> None:
    e = iniciar(M0, M1, mano=0)
    obs, acc = observacion_de(e, 0), acciones_legales(e)
    for accion_q in acciones_legales_q(obs, acc):
        assert a_concreta(accion_q, obs, acc) in acc


def test_clave_estado_es_discreta_y_estable() -> None:
    e = iniciar(M0, M1, mano=0)
    clave = clave_estado(observacion_de(e, 0))
    assert clave == ("libre", 2, 0, 0, 0, True)  # brava(2), tanto bajo(0), parejo, sin truco, mano


def test_agente_q_juega_partida_sin_romper() -> None:
    final = jugar_ronda(nueva_ronda(seed=1), (AgenteQ(QTable()), AgenteAleatorio(1)))
    assert final.terminada


def test_entrenar_mejora_el_winrate_vs_aleatorio() -> None:
    rival = lambda: AgenteAleatorio(seed=1)  # noqa: E731
    sin_entrenar = winrate_vs(QTable(), rival, partidas=200)
    tabla, _ = entrenar(episodios=12_000, rival=AgenteAleatorio(seed=1), seed=0)
    entrenado = winrate_vs(tabla, rival, partidas=200)
    assert entrenado > sin_entrenar
    assert entrenado > 0.75  # aprendió a ganarle holgado al azar
