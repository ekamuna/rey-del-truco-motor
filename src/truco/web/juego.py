"""Driver de una partida jugable *paso a paso* (para la web/API).

A diferencia de :func:`truco.partida.jugar_partida` (que corre la partida entera de
una), acá el humano juega de a una acción por request HTTP: el bot avanza solo hasta
que le toca al humano, y el estado se expone como un dict JSON-eable (:meth:`Juego.vista`).

El humano es el jugador 0. El bot (PIMC, con modelado del rival activado) es el 1.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from truco.agents.memoria_faroles import ConfigCazaFaroles, MemoriaFaroles
from truco.agents.pimc import AgentePIMC
from truco.core.engine import acciones_legales, actor, aplicar, nueva_ronda, observacion_de
from truco.core.state import EstadoRonda
from truco.trayectoria import Paso
from truco.ui.narrador import _label_accion, carta_str, narrar_evento, resumen_ronda

HUMANO = 0
BOT = 1


@dataclass
class Marcador:
    """Cuántas partidas ganó el humano y cuántas el bot (persistente)."""

    ganadas: int = 0
    perdidas: int = 0

    @classmethod
    def cargar(cls, ruta: Path) -> Marcador:
        try:
            d = json.loads(ruta.read_text())
            return cls(ganadas=int(d["ganadas"]), perdidas=int(d["perdidas"]))
        except (OSError, ValueError, KeyError):
            return cls()

    def guardar(self, ruta: Path) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({"ganadas": self.ganadas, "perdidas": self.perdidas}))


def _limpiar(linea: str) -> str:
    """Saca los marcadores de terminal (▸ ═ →) y el sangrado, para el log web."""
    return linea.strip().lstrip("▸═→·").strip()


class Juego:
    """Una partida completa a ``objetivo`` puntos, jugada de a una acción."""

    def __init__(self, marcador: Marcador, seed: int | None = None, objetivo: int = 15) -> None:
        self.marcador = marcador
        self.objetivo = objetivo
        self._rng = random.Random(seed)
        self.bot = AgentePIMC(
            seed=self._rng.randrange(2**31),
            config_caza=ConfigCazaFaroles(activar=True, p_mixing=0.30),
            memoria=MemoriaFaroles(),
            rival_id="humano",
        )
        self.puntos = (0, 0)  # marcador de ESTA partida (humano, bot)
        self.mano = HUMANO  # quién es mano esta ronda (alterna)
        self.terminada = False
        self.ganador: int | None = None
        self._contabilizada = False
        self.eventos: list[str] = []
        self.estado: EstadoRonda = self._nueva_ronda()

    # --- avance del juego -----------------------------------------------------

    def _nueva_ronda(self) -> EstadoRonda:
        self._traj: list[Paso] = []
        quien = "Sos mano" if self.mano == HUMANO else "Es mano la máquina"
        self.eventos.append(f"Nueva mano · {quien}")
        estado = nueva_ronda(
            seed=self._rng.randrange(2**31),
            mano=self.mano,
            puntos_partida=self.puntos,
            objetivo=self.objetivo,
        )
        self.estado = estado
        self._avanzar_bot()
        return self.estado

    def _avanzar_bot(self) -> None:
        while not self.estado.terminada and actor(self.estado) == BOT:
            obs = observacion_de(self.estado, BOT)
            accion = self.bot.actuar(obs, acciones_legales(self.estado))
            antes = self.estado
            self.estado = aplicar(self.estado, accion)
            self._traj.append(Paso(antes=antes, quien=BOT, accion=accion, despues=self.estado))
            self.eventos.extend(narrar_evento(antes, BOT, accion, self.estado, humano=HUMANO))
        if self.estado.terminada:
            self._cerrar_ronda()

    def _cerrar_ronda(self) -> None:
        self.eventos.extend(resumen_ronda(self.estado, humano=HUMANO))
        self.bot.observar_ronda(BOT, tuple(self._traj))
        pr = self.estado.puntos_ronda
        self.puntos = (self.puntos[0] + pr[0], self.puntos[1] + pr[1])
        if max(self.puntos) >= self.objetivo:
            self._terminar_partida()
        else:
            self.mano = 1 - self.mano
            self._nueva_ronda()

    def _terminar_partida(self) -> None:
        self.terminada = True
        self.ganador = HUMANO if self.puntos[0] > self.puntos[1] else BOT
        if not self._contabilizada:  # contabilizá una sola vez
            if self.ganador == HUMANO:
                self.marcador.ganadas += 1
            else:
                self.marcador.perdidas += 1
            self._contabilizada = True
        gane = "¡Ganaste la partida! 🎉" if self.ganador == HUMANO else "Ganó la máquina."
        self.eventos.append(gane)

    def jugar(self, indice: int) -> None:
        """Aplica la acción #``indice`` del humano y avanza hasta su próximo turno."""
        if self.terminada or self.estado.terminada or actor(self.estado) != HUMANO:
            return
        acciones = acciones_legales(self.estado)
        if not 0 <= indice < len(acciones):
            return
        self.eventos = []  # el log muestra sólo lo que pasó desde tu última jugada
        accion = acciones[indice]
        antes = self.estado
        self.estado = aplicar(self.estado, accion)
        self._traj.append(Paso(antes=antes, quien=HUMANO, accion=accion, despues=self.estado))
        self.eventos.extend(narrar_evento(antes, HUMANO, accion, self.estado, humano=HUMANO))
        self._avanzar_bot()

    # --- vista para la API ----------------------------------------------------

    def vista(self) -> dict[str, object]:
        tu_turno = (
            not self.terminada and not self.estado.terminada and actor(self.estado) == HUMANO
        )
        v: dict[str, object] = {
            "marcador": {"vos": self.marcador.ganadas, "bot": self.marcador.perdidas},
            "partida": {
                "vos": self.puntos[0],
                "bot": self.puntos[1],
                "objetivo": self.objetivo,
                "terminada": self.terminada,
                "ganador": self.ganador,
            },
            "eventos": [_limpiar(e) for e in self.eventos if _limpiar(e)],
            "tu_turno": tu_turno,
            "acciones": [],
        }
        if not self.terminada:
            obs = observacion_de(self.estado, HUMANO)
            carta_rival, carta_mia = obs.mesa[BOT], obs.mesa[HUMANO]
            v["ronda"] = {
                "mis_cartas": [carta_str(c) for c in obs.mi_mano],
                "mi_tanto": obs.mi_tanto,
                "soy_mano": obs.soy_mano,
                "carta_rival": carta_str(carta_rival) if carta_rival is not None else None,
                "carta_mia": carta_str(carta_mia) if carta_mia is not None else None,
            }
            if tu_turno:
                v["acciones"] = [
                    {"indice": i, "label": _label_accion(a), "tipo": a.tipo.value}
                    for i, a in enumerate(acciones_legales(self.estado))
                ]
        return v
