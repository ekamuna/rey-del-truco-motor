"""Tests del driver de la mini web app (partida paso a paso + marcador)."""

from pathlib import Path
from typing import Any

from truco.web.juego import Juego, Marcador, _limpiar


def test_marcador_persiste_round_trip(tmp_path: Path) -> None:
    ruta = tmp_path / "m.json"
    Marcador(ganadas=3, perdidas=2).guardar(ruta)
    assert Marcador.cargar(ruta) == Marcador(ganadas=3, perdidas=2)
    # archivo inexistente o roto → marcador en cero, sin explotar
    assert Marcador.cargar(tmp_path / "nope.json") == Marcador()


def test_vista_arranca_en_turno_del_humano() -> None:
    v: Any = Juego(Marcador(), seed=1).vista()
    assert {"marcador", "partida", "eventos", "tu_turno", "acciones"} <= set(v)
    assert v["tu_turno"] is True  # el humano arranca de mano
    assert len(v["acciones"]) >= 4  # 3 cartas + al menos un canto


def test_partida_completa_se_juega_hasta_el_final_y_cuenta() -> None:
    m = Marcador()
    j = Juego(m, seed=42, objetivo=15)
    for _ in range(5000):  # jugar siempre la primera acción legal hasta terminar
        if j.terminada:
            break
        v: Any = j.vista()
        assert v["tu_turno"], "tras cada jugada debe volver el turno al humano o terminar"
        j.jugar(int(v["acciones"][0]["indice"]))
    assert j.terminada
    assert j.ganador in (0, 1)
    assert max(j.puntos) >= 15
    assert m.ganadas + m.perdidas == 1  # se contabilizó exactamente una partida


def test_jugar_indice_invalido_no_rompe() -> None:
    j = Juego(Marcador(), seed=7)
    antes = j.vista()
    j.jugar(999)  # fuera de rango → no hace nada
    assert j.vista()["partida"] == antes["partida"]


def test_limpiar_saca_marcadores_de_terminal() -> None:
    assert _limpiar("  ▸ Vos tirás el 3 de espada") == "Vos tirás el 3 de espada"
    assert _limpiar("     ═ la mano es para vos") == "la mano es para vos"
