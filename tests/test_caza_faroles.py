"""Tests de la caza de faroles con memoria (bluff-catching honesto del envido)."""

from truco.agents.memoria_faroles import ConfigCazaFaroles, MemoriaFaroles
from truco.agents.pimc import AgentePIMC
from truco.agents.realistas import farolero_envido_real, pescador_real
from truco.agents.reglas import AgenteReglas
from truco.core.acciones import TipoAccion, canto
from truco.core.cards import Carta, Palo
from truco.core.engine import aplicar, iniciar
from truco.core.state import EstadoObservable
from truco.scoreboard import medir
from truco.trayectoria import Paso

TANTO_BAJO = (Carta(10, Palo.ORO), Carta(11, Palo.ORO), Carta(2, Palo.BASTO))  # tanto 20
CUALQUIERA = (Carta(5, Palo.COPA), Carta(6, Palo.COPA), Carta(7, Palo.BASTO))  # tanto 31


def _trayectoria_envido(respuesta: TipoAccion) -> tuple[Paso, ...]:
    """j0 (mano, tanto bajo 20) canta envido; j1 responde con ``respuesta``."""
    e0 = iniciar(TANTO_BAJO, CUALQUIERA, mano=0)
    e1 = aplicar(e0, canto(TipoAccion.ENVIDO))
    e2 = aplicar(e1, canto(respuesta))
    return (
        Paso(e0, 0, canto(TipoAccion.ENVIDO), e1),
        Paso(e1, 1, canto(respuesta), e2),
    )


def test_foldear_no_ensena_nada() -> None:
    # El rival cantó y el bot NO quiso → sin showdown → no se aprende (fix de la trampa).
    mem = MemoriaFaroles()
    mem.observar_ronda(1, _trayectoria_envido(TipoAccion.NO_QUIERO), ConfigCazaFaroles())
    assert mem.intentos("rival") == 0


def test_showdown_farol_se_cuenta() -> None:
    # El rival (mano, tanto 20) cantó y el bot QUISO → showdown → farol destapado.
    mem = MemoriaFaroles()
    cfg = ConfigCazaFaroles()
    mem.observar_ronda(1, _trayectoria_envido(TipoAccion.QUIERO), cfg)
    assert mem.conteos["rival"] == (1, 1)  # 1 farol en 1 showdown
    assert mem.estimar_farol("rival", cfg) > 0.5  # sube por encima del prior neutro


def test_activar_false_no_cambia_el_piso() -> None:
    # Con la caza apagada, el piso es el de siempre aunque haya memoria de farolero.
    mem = MemoriaFaroles(conteos={"rival": (8, 8)})
    ag_off = AgentePIMC(memoria=mem, config_caza=ConfigCazaFaroles(activar=False), rival_id="rival")
    ag_on = AgentePIMC(memoria=mem, config_caza=ConfigCazaFaroles(activar=True), rival_id="rival")
    assert ag_off._piso_ajustado_por_faroles(27) == 27
    assert ag_on._piso_ajustado_por_faroles(27) < 27  # con evidencia de farol, baja


def test_frecuencia_de_canto_baja_el_piso_sin_showdown() -> None:
    # Target #1: si el rival canta envido seguido (frecuencia alta), el piso baja AUNQUE
    # nunca se haya destapado un farol (sin showdown) → el bot le empieza a pagar los 26.
    cfg = ConfigCazaFaroles(activar=True)
    mem = MemoriaFaroles(cantos={"spammer": (9, 10)})  # cantó en 9 de 10 rondas
    ag = AgentePIMC(memoria=mem, config_caza=cfg, rival_id="spammer")
    assert ag._piso_ajustado_por_faroles(27) < 27  # baja sin ningún farol destapado
    # un rival que casi no canta (tight) no mueve el piso
    ag2 = AgentePIMC(
        memoria=MemoriaFaroles(cantos={"tight": (1, 10)}),
        config_caza=cfg,
        rival_id="tight",
    )
    assert ag2._piso_ajustado_por_faroles(27) == 27


def _obs_mano_paso(mi_tanto: int) -> EstadoObservable:
    """Soy pie (j1); el rival (mano) lideró la baza 1 sin cantar el envido."""
    return EstadoObservable(
        jugador=1,
        mi_mano=(Carta(4, Palo.BASTO),),
        mano=0,
        turno=1,
        mesa=(Carta(5, Palo.ORO), None),  # el mano ya jugó, yo no
        bazas=(),
        cartas_rival=2,
        pendiente=None,
        nivel_truco=0,
        truco_querido=False,
        envido_resuelto=False,
        puntos_partida=(0, 0),
        objetivo=15,
        terminada=False,
        ganador=None,
        puntos_ronda=(0, 0),
        mi_tanto=mi_tanto,
        tanto_rival=None,
    )


def test_regla1_default_canta_de_26_y_off_no_hace_nada() -> None:
    off = AgentePIMC(config_caza=ConfigCazaFaroles(activar=False))
    assert not off._value_cant_mano_paso(_obs_mano_paso(26))  # apagado → no hace nada
    on = AgentePIMC(config_caza=ConfigCazaFaroles(activar=True))
    assert on._value_cant_mano_paso(_obs_mano_paso(26))  # default 26 → canta de valor
    assert not on._value_cant_mano_paso(_obs_mano_paso(24))  # 24 < 26 → todavía no


def test_regla1_explota_a_23_si_confirmo_no_pescador() -> None:
    mem = MemoriaFaroles(pescas={"r": (0, 20)})  # 0 pescas en 20 → NO pescador
    ag = AgentePIMC(memoria=mem, config_caza=ConfigCazaFaroles(activar=True), rival_id="r")
    assert ag._value_cant_mano_paso(_obs_mano_paso(23))  # explota: baja la vara a 23


def test_regla1_no_explota_contra_pescador() -> None:
    mem = MemoriaFaroles(pescas={"r": (10, 20)})  # 50% pesca → PESCADOR
    ag = AgentePIMC(memoria=mem, config_caza=ConfigCazaFaroles(activar=True), rival_id="r")
    assert not ag._value_cant_mano_paso(_obs_mano_paso(24))  # se queda seguro (26)


def test_distingue_pescador_de_no_pescador_jugando() -> None:
    # El bot clasifica: el pescador tiene tasa de pesca ALTA, el honesto BAJA.
    cfg = ConfigCazaFaroles(activar=True)
    mem_p = MemoriaFaroles()
    medir(
        lambda: AgentePIMC(memoria=mem_p, config_caza=cfg, rival_id="p"),
        lambda: pescador_real(7),
        partidas=40,
        seed=11,
    )
    mem_h = MemoriaFaroles()
    medir(
        lambda: AgentePIMC(memoria=mem_h, config_caza=cfg, rival_id="h"),
        lambda: AgenteReglas(),
        partidas=40,
        seed=11,
    )
    assert mem_p.estimar_pesca("p", cfg) > mem_h.estimar_pesca("h", cfg)


def test_caza_mejora_el_winrate_vs_el_farolero() -> None:
    # El bot con memoria (compartida entre partidas) le gana MÁS al farolero de envido.
    sin = medir(lambda: AgentePIMC(), lambda: farolero_envido_real(7), partidas=60, seed=11)
    mem = MemoriaFaroles()
    cfg = ConfigCazaFaroles(activar=True, p_mixing=0.35)
    con = medir(
        lambda: AgentePIMC(memoria=mem, config_caza=cfg, rival_id="farolero"),
        lambda: farolero_envido_real(7),
        partidas=60,
        seed=11,
    )
    assert con.winrate > sin.winrate
    assert mem.intentos("farolero") > 0  # generó showdowns con el mixing
