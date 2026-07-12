"""CLI: jugá una PARTIDA completa (humano vs bot de reglas con perfil).

Ejecutar con::

    uv run truco                          # usuario "invitado"
    uv run truco --usuario emmanuel       # carga/guarda tu perfil
    uv run python -m truco.ui.cli --usuario emmanuel

El bot carga tu **historial** (``perfiles/<usuario>.json``), juega ajustándose a
tu fama y lo actualiza al terminar. La presentación vive en :mod:`truco.ui.narrador`.
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Callable
from pathlib import Path

from truco.agents.base import Agent
from truco.agents.reglas import AgenteReglas, ConfigReglas
from truco.core.acciones import Accion
from truco.core.engine import nueva_ronda
from truco.core.state import EstadoRonda
from truco.game_loop import jugar_ronda
from truco.perfil import Faceta, PerfilDelRival
from truco.perfil.almacen import AlmacenDePerfiles
from truco.rl.agente_q import AgenteQ
from truco.rl.qtable import QTable
from truco.ui.humano import AgenteHumano
from truco.ui.narrador import (
    encabezado_ronda,
    narrar_evento,
    resumen_partida,
    resumen_ronda,
)

OBJETIVO = 15

_ETIQUETAS_FAMA = {
    Faceta.MENTIROSO_TRUCO: "miente al truco",
    Faceta.MENTIROSO_ENVIDO: "miente al envido",
    Faceta.MIEDOSO: "se achica (no quiere el truco)",
}


def main(
    seed: int | None = None,
    escribir: Callable[[str], None] = print,
    usuario: str = "invitado",
    leer: Callable[[str], str] = input,
    almacen: AlmacenDePerfiles | None = None,
    rival: str = "reglas",
    modelo: str = "modelos/qtable.json",
) -> None:
    almacen = almacen or AlmacenDePerfiles()
    perfil = almacen.cargar(usuario)

    rng = random.Random(seed)
    humano = AgenteHumano(leer=leer, escribir=escribir)
    maquina = _crear_maquina(rival, perfil, rng, modelo, escribir)
    puntos = (0, 0)
    mano = 0
    numero = 0

    def narrar(antes: EstadoRonda, quien: int, accion: Accion, despues: EstadoRonda) -> None:
        for linea in narrar_evento(antes, quien, accion, despues):
            escribir(linea)

    escribir(f"═══ Rey del Truco — {usuario} vs la máquina · partida a {OBJETIVO} ═══")
    escribir(_fama(usuario, perfil))
    while max(puntos) < OBJETIVO:
        numero += 1
        escribir(encabezado_ronda(numero, mano))
        estado = nueva_ronda(
            seed=rng.randrange(2**31), mano=mano, puntos_partida=puntos, objetivo=OBJETIVO
        )
        estado = jugar_ronda(estado, (humano, maquina), al_actuar=narrar)
        for linea in resumen_ronda(estado):
            escribir(linea)
        puntos = (puntos[0] + estado.puntos_ronda[0], puntos[1] + estado.puntos_ronda[1])
        escribir(f"  Marcador de la partida:  vos {puntos[0]}  —  {puntos[1]} la máquina")
        mano = 1 - mano

    escribir(resumen_partida(puntos, OBJETIVO))
    almacen.guardar(perfil)
    escribir(_fama(usuario, perfil))


def _crear_maquina(
    rival: str,
    perfil: PerfilDelRival,
    rng: random.Random,
    modelo: str,
    escribir: Callable[[str], None],
) -> Agent:
    """Elige el oponente: el bot de reglas (con perfil + faroleo) o la IA entrenada."""
    if rival == "q":
        ruta = Path(modelo)
        if ruta.exists():
            escribir("Rival: IA entrenada por refuerzo (RL). 🤖")
            return AgenteQ(QTable.cargar(ruta))
        escribir(f"(No encontré el modelo {ruta}; entrenalo con 'uv run truco-entrenar'.)")
    # La máquina de reglas farolea (miente a veces): más seguido si te lee miedoso.
    return AgenteReglas(
        config=ConfigReglas(frecuencia_farol=0.25), perfil=perfil, seed=rng.randrange(2**31)
    )


def _fama(usuario: str, perfil: PerfilDelRival) -> str:
    """Resumen legible de lo que el bot cree saber del jugador."""
    lineas = [f"── Ficha de {usuario} ──"]
    hubo = False
    for faceta, texto in _ETIQUETAS_FAMA.items():
        total = perfil.intentos_global(faceta)
        if total == 0:
            continue
        hubo = True
        tasa = perfil.estimar_global(faceta)
        lineas.append(f"  · {texto}: ~{tasa:.0%}  ({total} jugadas vistas)")
    if not hubo:
        lineas.append("  (todavía te estoy conociendo…)")
    return "\n".join(lineas)


def cli() -> None:
    """Punto de entrada de consola: parsea argumentos y arranca la partida."""
    parser = argparse.ArgumentParser(description="Rey del Truco — jugá contra la máquina.")
    parser.add_argument(
        "--usuario", default="invitado", help="tu nombre de usuario (guarda tu perfil)"
    )
    parser.add_argument("--seed", type=int, default=None, help="semilla para reproducir la partida")
    parser.add_argument(
        "--rival",
        default="reglas",
        choices=["reglas", "q"],
        help="reglas (default) o q (IA entrenada)",
    )
    parser.add_argument("--modelo", default="modelos/qtable.json", help="ruta del modelo (rival q)")
    args = parser.parse_args()
    main(seed=args.seed, usuario=args.usuario, rival=args.rival, modelo=args.modelo)


if __name__ == "__main__":
    cli()
