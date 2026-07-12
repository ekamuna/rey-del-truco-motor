"""Tests de cálculo de tantos y valores de cantos (REGLAMENTO §4, §5)."""

from truco.core.acciones import TipoAccion
from truco.core.cards import Carta, Palo
from truco.core.scoring import (
    tanto_envido,
    valor_envido_no_querido,
    valor_envido_querido,
    valor_falta_envido,
)


def test_tanto_par_del_mismo_palo() -> None:
    # 5 y 3 de oro (+ 1 copa): 20 + 5 + 3 = 28.
    mano = (Carta(5, Palo.ORO), Carta(3, Palo.ORO), Carta(1, Palo.COPA))
    assert tanto_envido(mano) == 28


def test_tanto_maximo_33() -> None:
    mano = (Carta(6, Palo.ORO), Carta(7, Palo.ORO), Carta(4, Palo.COPA))
    assert tanto_envido(mano) == 33


def test_tanto_con_figuras_valen_cero() -> None:
    # Dos figuras del mismo palo: 20 + 0 + 0 = 20.
    mano = (Carta(12, Palo.ORO), Carta(10, Palo.ORO), Carta(4, Palo.COPA))
    assert tanto_envido(mano) == 20


def test_tanto_sin_par_es_la_carta_mas_alta() -> None:
    # Tres palos distintos: vale la carta más alta de envido (el 7).
    mano = (Carta(7, Palo.ORO), Carta(5, Palo.COPA), Carta(12, Palo.BASTO))
    assert tanto_envido(mano) == 7


def test_falta_envido_es_lo_que_falta_al_puntero() -> None:
    assert valor_falta_envido((22, 10), objetivo=30) == 8
    assert valor_falta_envido((10, 22), objetivo=30) == 8
    assert valor_falta_envido((29, 0), objetivo=30) == 1
    assert valor_falta_envido((30, 30), objetivo=30) == 1  # mínimo 1


def test_valor_envido_querido() -> None:
    e = (TipoAccion.ENVIDO,)
    assert valor_envido_querido(e, valor_falta=15) == 2
    ee = (TipoAccion.ENVIDO, TipoAccion.ENVIDO)
    assert valor_envido_querido(ee, valor_falta=15) == 4
    er = (TipoAccion.ENVIDO, TipoAccion.REAL_ENVIDO)
    assert valor_envido_querido(er, valor_falta=15) == 5
    f = (TipoAccion.ENVIDO, TipoAccion.FALTA_ENVIDO)
    assert valor_envido_querido(f, valor_falta=15) == 15  # la falta manda


def test_valor_envido_no_querido() -> None:
    assert valor_envido_no_querido((TipoAccion.ENVIDO,)) == 1
    assert valor_envido_no_querido((TipoAccion.REAL_ENVIDO,)) == 1
    assert valor_envido_no_querido((TipoAccion.ENVIDO, TipoAccion.REAL_ENVIDO)) == 2
    assert valor_envido_no_querido((TipoAccion.REAL_ENVIDO, TipoAccion.FALTA_ENVIDO)) == 3
