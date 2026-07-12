"""Tests del faroleo del bot: mentir con mano fea, modulado por el perfil."""

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.reglas import AgenteReglas, ConfigReglas
from truco.core.acciones import TipoAccion
from truco.core.cards import Carta, Palo
from truco.core.engine import acciones_legales, iniciar, observacion_de
from truco.partida import jugar_partida
from truco.perfil import PerfilDelRival

# Mano fea: mejor carta = rey (fuerza 6 < 10) y tanto 5 (< 23 → sin farol de envido).
FLOJA = (Carta(12, Palo.ORO), Carta(4, Palo.COPA), Carta(5, Palo.BASTO))
RIVAL = (Carta(1, Palo.ESPADA), Carta(2, Palo.ORO), Carta(3, Palo.COPA))


def _decidir(bot: AgenteReglas) -> TipoAccion:
    e = iniciar(FLOJA, RIVAL, mano=0)
    return bot.actuar(observacion_de(e, 0), acciones_legales(e)).tipo


def test_sin_frecuencia_no_farolea() -> None:
    # Por defecto (frecuencia 0), con mano fea juega una carta: no miente.
    assert _decidir(AgenteReglas()) is TipoAccion.JUGAR


def test_con_frecuencia_total_farolea_el_truco() -> None:
    bot = AgenteReglas(ConfigReglas(frecuencia_farol=1.0), seed=0)
    assert _decidir(bot) is TipoAccion.TRUCO


def test_farol_reproducible_con_semilla() -> None:
    def secuencia(seed: int) -> list[TipoAccion]:
        bot = AgenteReglas(ConfigReglas(frecuencia_farol=0.5), seed=seed)
        e = iniciar(FLOJA, RIVAL, mano=0)
        obs, acc = observacion_de(e, 0), acciones_legales(e)
        return [bot.actuar(obs, acc).tipo for _ in range(20)]

    assert secuencia(7) == secuencia(7)  # misma semilla → misma tanda de mentiras
    assert secuencia(7) != secuencia(8)  # semillas distintas → tandas distintas


def test_farolea_mas_al_miedoso_que_al_que_paga_para_ver() -> None:
    def faroles(perfil: PerfilDelRival, n: int = 200) -> int:
        bot = AgenteReglas(ConfigReglas(frecuencia_farol=0.5), perfil=perfil, seed=1)
        e = iniciar(FLOJA, RIVAL, mano=0)
        obs, acc = observacion_de(e, 0), acciones_legales(e)
        return sum(bot.actuar(obs, acc).tipo is TipoAccion.TRUCO for _ in range(n))

    miedoso = PerfilDelRival("miedoso")
    miedoso.conteos["miedoso|parejo"] = (9, 10)  # se achica seguido
    paga = PerfilDelRival("paga")
    paga.conteos["miedoso|parejo"] = (0, 10)  # nunca se achica

    assert faroles(miedoso) > faroles(paga)


def test_bot_farolero_juega_partidas_sin_romper() -> None:
    bot = AgenteReglas(ConfigReglas(frecuencia_farol=0.3), seed=5)
    r = jugar_partida((bot, AgenteAleatorio(1)), objetivo=15, seed=2)
    assert r.ganador in (0, 1)
