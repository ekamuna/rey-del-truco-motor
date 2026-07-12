"""Tests del narrador de la UI (presentación pura)."""

from truco.core.acciones import TipoAccion, canto, jugar_carta
from truco.core.cards import Carta, Palo
from truco.core.engine import aplicar, iniciar, observacion_de
from truco.ui.narrador import (
    carta_str,
    encabezado_ronda,
    menu,
    narrar_evento,
    resumen_partida,
    resumen_ronda,
    tablero,
)

# j0: 5+3 de oro = 28 · j1: 7+11 de copa = 27
MANO_28 = (Carta(5, Palo.ORO), Carta(3, Palo.ORO), Carta(1, Palo.COPA))
MANO_27 = (Carta(7, Palo.COPA), Carta(11, Palo.COPA), Carta(10, Palo.ORO))
# Para bazas claras.
MACHO = Carta(1, Palo.ESPADA)
G0 = (MACHO, Carta(1, Palo.BASTO), Carta(4, Palo.ESPADA))
G1 = (Carta(12, Palo.ORO), Carta(5, Palo.ORO), Carta(6, Palo.ORO))


def _texto(lineas: list[str]) -> str:
    return "\n".join(lineas)


def test_carta_str_incluye_simbolo_de_palo() -> None:
    assert carta_str(Carta(3, Palo.ESPADA)) == "3 de espada ♠"
    assert "♦" in carta_str(Carta(12, Palo.ORO))


def test_narrar_canto_distingue_vos_y_maquina() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    e2 = aplicar(e, canto(TipoAccion.ENVIDO))
    vos = _texto(narrar_evento(e, 0, canto(TipoAccion.ENVIDO), e2))
    assert "Vos" in vos and "ENVIDO" in vos
    # la máquina cantando (real envido como respuesta)
    e3 = aplicar(e2, canto(TipoAccion.REAL_ENVIDO))
    maq = _texto(narrar_evento(e2, 1, canto(TipoAccion.REAL_ENVIDO), e3))
    assert "La máquina" in maq and "REAL ENVIDO" in maq


def test_envido_querido_muestra_tantos_ganador_y_puntos() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    e2 = aplicar(e, canto(TipoAccion.ENVIDO))  # j0 canta
    e3 = aplicar(e2, canto(TipoAccion.QUIERO))  # j1 quiere
    texto = _texto(narrar_evento(e2, 1, canto(TipoAccion.QUIERO), e3))
    assert "28" in texto and "27" in texto  # los dos tantos
    assert "vos" in texto  # gana el envido vos (28 > 27)
    assert "+2" in texto  # puntos del envido


def test_envido_no_querido_no_revela_los_tantos() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    e2 = aplicar(e, canto(TipoAccion.ENVIDO))
    e3 = aplicar(e2, canto(TipoAccion.NO_QUIERO))
    texto = _texto(narrar_evento(e2, 1, canto(TipoAccion.NO_QUIERO), e3))
    assert "+1" in texto and "vos" in texto  # el cantor (vos) se lleva 1
    assert "28" not in texto and "27" not in texto  # nadie mostró las cartas


def test_narrar_baza_dice_la_carta_y_quien_gano() -> None:
    e = iniciar(G0, G1, mano=0)
    e2 = aplicar(e, jugar_carta(MACHO))  # j0 tira el macho
    e3 = aplicar(e2, jugar_carta(Carta(12, Palo.ORO)))  # j1 tira el 12 → gana j0
    texto = _texto(narrar_evento(e2, 1, jugar_carta(Carta(12, Palo.ORO)), e3))
    assert "12 de oro" in texto
    assert "la mano es para vos" in texto


def test_truco_querido_anuncia_por_cuanto_se_juega() -> None:
    e = iniciar(G0, G1, mano=0)
    e2 = aplicar(e, canto(TipoAccion.TRUCO))
    e3 = aplicar(e2, canto(TipoAccion.QUIERO))
    texto = _texto(narrar_evento(e2, 1, canto(TipoAccion.QUIERO), e3))
    assert "se juega por 2" in texto


def test_tablero_muestra_marcador_y_cartas() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0, puntos_partida=(3, 4), objetivo=15)
    txt = tablero(observacion_de(e, 0))
    assert "Tus cartas" in txt  # (compatibilidad con test del agente humano)
    assert "vos 3" in txt and "4 la máquina" in txt
    assert "tu envido: 28" in txt


def test_menu_lista_las_acciones() -> None:
    e = iniciar(MANO_28, MANO_27, mano=0)
    from truco.core.engine import acciones_legales

    txt = menu(acciones_legales(e))
    assert "[0]" in txt and "jugar" in txt
    assert "ENVIDO" in txt


def test_resumen_ronda_desglosa_envido_y_truco() -> None:
    # j0 canta envido y gana; luego gana las bazas → desglose envido + truco.
    e = iniciar(G0, MANO_27, mano=0)
    e = aplicar(e, canto(TipoAccion.ENVIDO))
    e = aplicar(e, canto(TipoAccion.QUIERO))  # envido para... comparamos tantos
    # jugar las 3 cartas: G0 gana con las bravas
    e = aplicar(e, jugar_carta(MACHO))
    e = aplicar(e, jugar_carta(Carta(7, Palo.COPA)))
    e = aplicar(e, jugar_carta(Carta(1, Palo.BASTO)))
    e = aplicar(e, jugar_carta(Carta(11, Palo.COPA)))
    assert e.terminada
    texto = _texto(resumen_ronda(e))
    assert "Envido" in texto and "Truco" in texto
    assert "Ganó la mano" in texto


def test_encabezado_y_resumen_partida() -> None:
    assert "arranca vos" in encabezado_ronda(1, mano=0)
    assert "arranca la máquina" in encabezado_ronda(2, mano=1)
    assert "GANASTE" in resumen_partida((15, 8), 15)
    assert "Ganó la máquina" in resumen_partida((9, 15), 15)
