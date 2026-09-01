"""Tests de la red neuronal (M7): encoder, máscara, red y AgenteRed."""
# ruff: noqa: E402  (importorskip debe correr ANTES de importar torch/numpy/rl)
import pytest

pytest.importorskip("torch")
pytest.importorskip("numpy")

import torch

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.estilos import agresivo, conservador, mentiroso
from truco.core.acciones import TipoAccion, canto
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, aplicar, iniciar, nueva_ronda, observacion_de
from truco.game_loop import jugar_ronda
from truco.partida import jugar_partida
from truco.rl.agente_red import AgenteRed
from truco.rl.encoder import (
    DIM,
    N_ACCIONES,
    accion_desde_indice,
    codificar,
    indice_de_accion,
    mascara_legal,
)
from truco.rl.red import PoliticaValor, logits_enmascarados

M0 = (Carta(1, Palo.ESPADA), Carta(4, Palo.ORO), Carta(5, Palo.ESPADA))
M1 = (Carta(1, Palo.BASTO), Carta(4, Palo.ESPADA), Carta(5, Palo.ORO))


def test_encoder_dim_consistente() -> None:
    e = iniciar(M0, M1, mano=0)
    vector = codificar(observacion_de(e, 0))
    assert vector.shape == (DIM,)
    assert vector.dtype.name == "float32"


def test_mascara_marca_solo_lo_legal() -> None:
    e = iniciar(M0, M1, mano=0)
    acc = acciones_legales(e)
    mascara = mascara_legal(acc)
    assert mascara.sum() == len(acc)
    for a in acc:
        assert mascara[indice_de_accion(a)]


def test_accion_desde_indice_devuelve_legal() -> None:
    e = aplicar(iniciar(M0, M1, mano=0), canto(TipoAccion.ENVIDO))  # responde j1
    acc = acciones_legales(e)
    for a in acc:
        assert accion_desde_indice(indice_de_accion(a), acc) == a


def test_red_forward_da_formas_correctas() -> None:
    red = PoliticaValor()
    x = torch.zeros(4, DIM)
    logits, valores = red(x)
    assert logits.shape == (4, N_ACCIONES)
    assert valores.shape == (4,)


def test_enmascarado_anula_ilegales() -> None:
    logits = torch.zeros(1, N_ACCIONES)
    mascara = torch.zeros(1, N_ACCIONES, dtype=torch.bool)
    mascara[0, 5] = True
    enmascarados = logits_enmascarados(logits, mascara)
    assert enmascarados[0, 5] == 0.0
    assert enmascarados[0, 0] < -1e8  # ilegal → -inf


def test_agente_red_sin_entrenar_juega_legal() -> None:
    # La máscara garantiza jugadas legales aunque la red no esté entrenada:
    # si eligiera una ilegal, el bucle lanzaría error.
    agente = AgenteRed(PoliticaValor())
    for s in range(15):
        final = jugar_ronda(nueva_ronda(seed=s), (agente, AgenteAleatorio(s)))
        assert final.terminada


def test_estilos_juegan_partidas() -> None:
    for fabrica in (agresivo, mentiroso, conservador):
        r = jugar_partida((fabrica(1), AgenteAleatorio(2)), objetivo=15, seed=1)
        assert r.ganador in (0, 1)


def test_red_guarda_y_carga(tmp_path) -> None:  # type: ignore[no-untyped-def]
    ruta = tmp_path / "red.pt"
    torch.save(PoliticaValor().state_dict(), ruta)
    agente = AgenteRed.cargar(ruta)
    final = jugar_ronda(nueva_ronda(seed=1), (agente, AgenteAleatorio(1)))
    assert final.terminada
