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

from truco.agents.reglas import AgenteReglas
from truco.core.acciones import Accion
from truco.core.engine import nueva_ronda
from truco.core.state import EstadoRonda
from truco.game_loop import jugar_ronda
from truco.perfil import Faceta, PerfilDelRival
from truco.perfil.almacen import AlmacenDePerfiles
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
) -> None:
    almacen = almacen or AlmacenDePerfiles()
    perfil = almacen.cargar(usuario)

    humano = AgenteHumano(leer=leer, escribir=escribir)
    maquina = AgenteReglas(perfil=perfil)
    rng = random.Random(seed)
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
    args = parser.parse_args()
    main(seed=args.seed, usuario=args.usuario)


if __name__ == "__main__":
    cli()
