"""Tests del PerfilDelRival: prior, actualización desde la trayectoria y globales."""

from truco.core.acciones import Accion, TipoAccion, canto
from truco.core.cards import Carta, Palo
from truco.core.engine import actor, aplicar, iniciar
from truco.core.state import EstadoRonda
from truco.perfil import ConfigPerfil, Contexto, Faceta, PerfilDelRival
from truco.trayectoria import Paso

DEBIL = (Carta(4, Palo.ORO), Carta(5, Palo.COPA), Carta(6, Palo.BASTO))  # fuerza máx 2, tanto 6
FUERTE = (Carta(1, Palo.ESPADA), Carta(2, Palo.ORO), Carta(3, Palo.COPA))  # brava, tanto alto


def reproducir(estado: EstadoRonda, acciones: list[Accion]) -> tuple[Paso, ...]:
    pasos = []
    for accion in acciones:
        quien = actor(estado)
        antes = estado
        estado = aplicar(estado, accion)
        pasos.append(Paso(antes=antes, quien=quien, accion=accion, despues=estado))
    return tuple(pasos)


def test_prior_neutral_sin_datos() -> None:
    p = PerfilDelRival("x")
    assert abs(p.estimar(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) - 0.30) < 0.01
    assert p.intentos(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) == 0


def test_registra_mentiroso_truco_con_mano_debil() -> None:
    e = iniciar(FUERTE, DEBIL, mano=1)  # j1 (débil) es mano y actúa primero
    tray = reproducir(e, [canto(TipoAccion.TRUCO)])  # j1 canta truco de mentira
    p = PerfilDelRival("x")
    p.actualizar(1, tray)
    assert p.intentos(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) == 1
    # con 1 mentira de 1, la estimación sube por encima del prior
    assert p.estimar(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) > 0.30


def test_no_registra_mentira_si_la_mano_es_fuerte() -> None:
    e = iniciar(DEBIL, FUERTE, mano=1)  # j1 fuerte canta truco (NO es mentira)
    tray = reproducir(e, [canto(TipoAccion.TRUCO)])
    p = PerfilDelRival("x")
    p.actualizar(1, tray)
    assert p.intentos(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) == 1
    # 0 mentiras de 1 → estimación por debajo del prior
    assert p.estimar(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) < 0.30


def test_registra_mentiroso_envido_con_tanto_bajo() -> None:
    e = iniciar(FUERTE, DEBIL, mano=1)  # j1 tanto 6 canta envido
    tray = reproducir(e, [canto(TipoAccion.ENVIDO)])
    p = PerfilDelRival("x")
    p.actualizar(1, tray)
    assert p.intentos(Faceta.MENTIROSO_ENVIDO, Contexto.PAREJO) == 1
    assert p.estimar(Faceta.MENTIROSO_ENVIDO, Contexto.PAREJO) > 0.30


def test_registra_miedoso_al_no_querer_el_truco() -> None:
    e = iniciar(FUERTE, DEBIL, mano=0)  # j0 canta truco, j1 responde
    tray = reproducir(e, [canto(TipoAccion.TRUCO), canto(TipoAccion.NO_QUIERO)])
    p = PerfilDelRival("x")
    p.actualizar(1, tray)
    assert p.intentos(Faceta.MIEDOSO, Contexto.PAREJO) == 1
    assert p.estimar(Faceta.MIEDOSO, Contexto.PAREJO) > 0.30


def test_querer_el_truco_cuenta_pero_no_como_miedo() -> None:
    e = iniciar(FUERTE, DEBIL, mano=0)
    tray = reproducir(e, [canto(TipoAccion.TRUCO), canto(TipoAccion.QUIERO)])
    p = PerfilDelRival("x")
    p.actualizar(1, tray)
    assert p.intentos(Faceta.MIEDOSO, Contexto.PAREJO) == 1  # enfrentó el truco
    assert p.estimar(Faceta.MIEDOSO, Contexto.PAREJO) < 0.30  # pero no se achicó


def test_contexto_segun_marcador() -> None:
    # j1 va perdiendo por 5 → sus jugadas se registran en el contexto PERDIENDO.
    e = iniciar(FUERTE, DEBIL, mano=1, puntos_partida=(8, 3), objetivo=15)
    tray = reproducir(e, [canto(TipoAccion.TRUCO)])
    p = PerfilDelRival("x")
    p.actualizar(1, tray)
    assert p.intentos(Faceta.MENTIROSO_TRUCO, Contexto.PERDIENDO) == 1
    assert p.intentos(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) == 0


def test_estimacion_global_agrupa_contextos() -> None:
    p = PerfilDelRival("x")
    p.conteos["mentiroso_truco|parejo"] = (2, 4)
    p.conteos["mentiroso_truco|perdiendo"] = (3, 4)
    assert p.intentos_global(Faceta.MENTIROSO_TRUCO) == 8
    # (2+3 + 1.5) / (8 + 5) = 6.5/13 = 0.5
    assert abs(p.estimar_global(Faceta.MENTIROSO_TRUCO) - 0.5) < 0.01


# --- Configurabilidad ---------------------------------------------------------


def test_prior_configurable() -> None:
    p = PerfilDelRival("x", config=ConfigPerfil(prior_alfa=5.0, prior_beta=5.0))
    assert abs(p.estimar(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) - 0.5) < 0.01  # 5/10


def test_definicion_de_mano_debil_configurable() -> None:
    # Mano cuyo mejor carta es un 3 (fuerza 9). Cantó truco con eso.
    mano_con_tres = (Carta(3, Palo.ORO), Carta(4, Palo.COPA), Carta(5, Palo.BASTO))
    tray = reproducir(iniciar(FUERTE, mano_con_tres, mano=1), [canto(TipoAccion.TRUCO)])

    laxo = PerfilDelRival("a", config=ConfigPerfil(fuerza_mano_debil=8))
    laxo.actualizar(1, tray)
    estricto = PerfilDelRival("b", config=ConfigPerfil(fuerza_mano_debil=10))
    estricto.actualizar(1, tray)

    # Con umbral 8, un 3 (fuerza 9) NO es débil → no es mentira → baja.
    assert laxo.estimar(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) < 0.30
    # Con umbral 10 (exige brava), un 3 SÍ es débil → es mentira → sube.
    assert estricto.estimar(Faceta.MENTIROSO_TRUCO, Contexto.PAREJO) > 0.30
