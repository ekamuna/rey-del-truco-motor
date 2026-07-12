"""Tests del envido en el motor (REGLAMENTO §4)."""

from truco.core.acciones import TipoAccion, canto, jugar_carta
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, aplicar, iniciar

# j0: 5+3 de oro = 28 · j1: 7+11 de copa = 27
MANO_28 = (Carta(5, Palo.ORO), Carta(3, Palo.ORO), Carta(1, Palo.COPA))
MANO_27 = (Carta(7, Palo.COPA), Carta(11, Palo.COPA), Carta(10, Palo.ORO))
# Dos manos con tanto 20 (par de figuras del mismo palo).
MANO_20A = (Carta(12, Palo.ORO), Carta(10, Palo.ORO), Carta(4, Palo.COPA))
MANO_20B = (Carta(11, Palo.BASTO), Carta(10, Palo.BASTO), Carta(4, Palo.ESPADA))


def test_envido_querido_lo_gana_el_mayor_tanto() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    e = aplicar(e, canto(TipoAccion.ENVIDO))
    e = aplicar(e, canto(TipoAccion.QUIERO))
    assert e.envido_resuelto
    assert e.envido_ganador == 0
    assert e.puntos_ronda == (2, 0)


def test_envido_no_querido_da_un_punto_al_cantor() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    e = aplicar(e, canto(TipoAccion.ENVIDO))
    e = aplicar(e, canto(TipoAccion.NO_QUIERO))
    assert e.envido_resuelto
    assert e.puntos_ronda == (1, 0)


def test_empate_de_tanto_gana_el_mano() -> None:
    e = iniciar(MANO_20A, MANO_20B, mano=1)  # el mano es j1
    e = aplicar(e, canto(TipoAccion.ENVIDO))  # lo canta j1 (es mano y turno)
    e = aplicar(e, canto(TipoAccion.QUIERO))
    assert e.envido_ganador == 1


def test_cadena_envido_real_envido() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    e = aplicar(e, canto(TipoAccion.ENVIDO))  # j0
    e = aplicar(e, canto(TipoAccion.REAL_ENVIDO))  # j1 sube
    e = aplicar(e, canto(TipoAccion.QUIERO))  # j0 quiere
    assert e.puntos_ronda == (2 + 3, 0)  # 5 al ganador (j0, 28 > 27)


def test_real_envido_no_querido_da_un_punto() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    e = aplicar(e, canto(TipoAccion.REAL_ENVIDO))  # j0 canta real directo
    e = aplicar(e, canto(TipoAccion.NO_QUIERO))  # j1 no quiere
    assert e.puntos_ronda == (1, 0)


def test_envido_disponible_solo_en_primera_baza() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    tipos = {a.tipo for a in acciones_legales(e)}
    assert TipoAccion.ENVIDO in tipos
    # j0 juega; el envido sigue disponible para j1 (que no jugó)
    e = aplicar(e, jugar_carta(MANO_28[0]))
    assert TipoAccion.ENVIDO in {a.tipo for a in acciones_legales(e)}
    # j1 juega y se cierra la primera baza: ya no hay envido
    e = aplicar(e, jugar_carta(MANO_27[0]))
    assert TipoAccion.ENVIDO not in {a.tipo for a in acciones_legales(e)}


def test_falta_envido_vale_lo_que_falta_al_puntero() -> None:
    # Partida a 15, puntero en 10 → falta = 5.
    e = iniciar(MANO_28, MANO_27, mano=0, puntos_partida=(10, 3), objetivo=15)
    e = aplicar(e, canto(TipoAccion.FALTA_ENVIDO))
    e = aplicar(e, canto(TipoAccion.QUIERO))
    assert e.puntos_ronda == (5, 0)  # j0 gana el envido y se lleva la falta (5)
