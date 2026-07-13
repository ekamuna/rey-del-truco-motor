"""Tests de la caza de faroles con memoria (bluff-catching honesto del envido)."""

from truco.agents.memoria_faroles import ConfigCazaFaroles, MemoriaFaroles
from truco.agents.pimc import AgentePIMC
from truco.agents.realistas import farolero_envido_real
from truco.core.acciones import TipoAccion, canto
from truco.core.cards import Carta, Palo
from truco.core.engine import aplicar, iniciar
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
