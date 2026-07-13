"""Autopsia de derrotas: juega partidos, guarda los que el bot **pierde** con la
trayectoria completa de cada ronda, y los renderiza como transcripción legible
para que una IA diagnostique *por qué* se perdió y proponga reglas.

Referencia: ``docs/NORTE.md`` (T5, loop de autopsia). La transcripción revela las
DOS manos (en la autopsia sí tenemos info perfecta): así se puede juzgar si el bot
jugó mal o fue mala suerte del reparto (comparable contra el oráculo).
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from truco.agents.base import Agent
from truco.core.acciones import Accion
from truco.core.cards import Carta
from truco.core.engine import nueva_ronda
from truco.core.state import EstadoRonda
from truco.game_loop import jugar_ronda
from truco.trayectoria import Paso

FabricaAgente = Callable[[], Agent]


@dataclass(frozen=True, slots=True)
class RondaJugada:
    inicial: EstadoRonda
    pasos: tuple[Paso, ...]
    final: EstadoRonda


@dataclass(frozen=True, slots=True)
class PartidoJugado:
    puntos: tuple[int, int]
    ganador: int
    rondas: tuple[RondaJugada, ...]
    seed: int
    mano_inicial: int


class _Grabador:
    """Callback ``al_actuar`` que acumula los pasos de una ronda."""

    def __init__(self) -> None:
        self.pasos: list[Paso] = []

    def __call__(
        self, antes: EstadoRonda, quien: int, accion: Accion, despues: EstadoRonda
    ) -> None:
        self.pasos.append(Paso(antes=antes, quien=quien, accion=accion, despues=despues))


def _jugar_partido_capturando(
    agentes: tuple[Agent, Agent],
    seed: int,
    mano_inicial: int,
    objetivo: int = 15,
    max_rondas: int = 1000,
) -> PartidoJugado:
    """Como ``jugar_partida`` pero guardando la trayectoria de cada ronda."""
    rng = random.Random(seed)
    puntos = (0, 0)
    mano = mano_inicial
    rondas: list[RondaJugada] = []
    while max(puntos) < objetivo and len(rondas) < max_rondas:
        inicial = nueva_ronda(
            seed=rng.randrange(2**31), mano=mano, puntos_partida=puntos, objetivo=objetivo
        )
        grab = _Grabador()
        final = jugar_ronda(inicial, agentes, al_actuar=grab)
        rondas.append(RondaJugada(inicial=inicial, pasos=tuple(grab.pasos), final=final))
        puntos = (puntos[0] + final.puntos_ronda[0], puntos[1] + final.puntos_ronda[1])
        mano = 1 - mano
    ganador = 0 if puntos[0] > puntos[1] else 1
    return PartidoJugado(
        puntos=puntos, ganador=ganador, rondas=tuple(rondas), seed=seed, mano_inicial=mano_inicial
    )


def recolectar_derrotas(
    bot: FabricaAgente,
    rival: FabricaAgente,
    partidas: int,
    seed: int,
    objetivo: int = 15,
) -> list[PartidoJugado]:
    """Juega ``partidas`` (bot = jugador 0) y devuelve sólo los partidos perdidos."""
    rng = random.Random(seed)
    derrotas: list[PartidoJugado] = []
    for i in range(partidas):
        partido = _jugar_partido_capturando(
            (bot(), rival()), seed=rng.randrange(2**31), mano_inicial=i % 2, objetivo=objetivo
        )
        if partido.ganador != 0:
            derrotas.append(partido)
    return derrotas


# --- Renderizado legible para la IA -----------------------------------------


def _q(jugador: int) -> str:
    return "BOT" if jugador == 0 else "RIV"


def _mano_str(cartas: tuple[Carta, ...]) -> str:
    return ", ".join(str(c) for c in cartas)


def render_ronda(ronda: RondaJugada, k: int) -> str:
    ini, fin = ronda.inicial, ronda.final
    lineas = [
        f"— Ronda {k} | mano: {_q(ini.mano)} | marcador antes BOT {ini.puntos_partida[0]}"
        f"–{ini.puntos_partida[1]} RIV",
        f"    BOT  mano: [{_mano_str(ini.manos[0])}]  (envido {ini.tantos[0]})",
        f"    RIV  mano: [{_mano_str(ini.manos[1])}]  (envido {ini.tantos[1]})",
    ]
    for paso in ronda.pasos:
        lineas.append(f"      {_q(paso.quien)}: {paso.accion}")
    envido = ""
    if fin.envido_ganador is not None:
        envido = f" | envido→{_q(fin.envido_ganador)} (+{fin.puntos_envido})"
    lineas.append(
        f"    => ronda BOT +{fin.puntos_ronda[0]} / RIV +{fin.puntos_ronda[1]}"
        f"  [{fin.motivo}]{envido}"
    )
    return "\n".join(lineas)


def render_partido(partido: PartidoJugado, titulo: str = "") -> str:
    cab = (
        f"=== PARTIDO PERDIDO {titulo}  final BOT {partido.puntos[0]}–{partido.puntos[1]} RIV"
        f"  (mano inicial: {'BOT' if partido.mano_inicial == 0 else 'RIV'}) ==="
    )
    cuerpo = "\n".join(render_ronda(r, k + 1) for k, r in enumerate(partido.rondas))
    return f"{cab}\n{cuerpo}"


def main() -> None:
    import argparse

    from truco.agents.estilos import agresivo, conservador, mentiroso
    from truco.agents.pimc import AgentePIMC
    from truco.agents.reglas import AgenteReglas

    rivales: dict[str, FabricaAgente] = {
        "reglas": lambda: AgenteReglas(),
        "conservador": lambda: conservador(7),
        "agresivo": lambda: agresivo(7),
        "mentiroso": lambda: mentiroso(7),
    }
    parser = argparse.ArgumentParser(description="Autopsia de derrotas del PIMC")
    parser.add_argument("--rival", choices=list(rivales), default="agresivo")
    parser.add_argument("--partidas", type=int, default=40)
    parser.add_argument("--mostrar", type=int, default=3, help="cuántas derrotas imprimir")
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()

    derrotas = recolectar_derrotas(
        lambda: AgentePIMC(), rivales[args.rival], partidas=args.partidas, seed=args.seed
    )
    print(f"Perdidos {len(derrotas)}/{args.partidas} vs {args.rival}\n")
    for partido in derrotas[: args.mostrar]:
        print(render_partido(partido, titulo=f"vs {args.rival}"))
        print()
