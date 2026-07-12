"""Tests del tipo Accion y sus atajos."""

import pytest

from truco.core.acciones import (
    CANTOS_ENVIDO,
    CANTOS_TRUCO,
    CATEGORIA_ENVIDO,
    CATEGORIA_TRUCO,
    Accion,
    TipoAccion,
    canto,
    categoria_de,
    jugar_carta,
)
from truco.core.cards import Carta, Palo


def test_jugar_requiere_carta() -> None:
    with pytest.raises(ValueError):
        Accion(TipoAccion.JUGAR)


def test_canto_no_lleva_carta() -> None:
    with pytest.raises(ValueError):
        Accion(TipoAccion.TRUCO, Carta(1, Palo.ESPADA))


def test_atajos() -> None:
    c = Carta(1, Palo.ESPADA)
    assert jugar_carta(c) == Accion(TipoAccion.JUGAR, c)
    assert canto(TipoAccion.QUIERO) == Accion(TipoAccion.QUIERO)


def test_categoria_de() -> None:
    for t in CANTOS_ENVIDO:
        assert categoria_de(t) == CATEGORIA_ENVIDO
    for t in CANTOS_TRUCO:
        assert categoria_de(t) == CATEGORIA_TRUCO
    with pytest.raises(ValueError):
        categoria_de(TipoAccion.QUIERO)


def test_str_legible() -> None:
    assert str(jugar_carta(Carta(7, Palo.ORO))) == "jugar 7 de oro"
    assert str(canto(TipoAccion.REAL_ENVIDO)) == "real envido"
