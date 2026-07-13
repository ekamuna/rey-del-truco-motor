"""AgenteRed — juega con una red neuronal entrenada (política greedy).

Misma interfaz :class:`Agent` que todos: se enchufa al bucle, partida y evaluación
sin cambiar nada. Elige la acción legal de mayor puntaje según la red.
"""

from __future__ import annotations

from pathlib import Path

import torch

from truco.agents.base import Agent
from truco.core.acciones import Accion
from truco.core.state import EstadoObservable
from truco.rl.encoder import accion_desde_indice, codificar, mascara_legal
from truco.rl.red import PoliticaValor, logits_enmascarados


class AgenteRed(Agent):
    def __init__(self, red: PoliticaValor, device: str = "cpu") -> None:
        self.red = red
        self.device = device
        self.red.eval()

    def actuar(self, obs: EstadoObservable, acciones: tuple[Accion, ...]) -> Accion:
        x = torch.from_numpy(codificar(obs)).to(self.device).unsqueeze(0)
        mascara = torch.from_numpy(mascara_legal(acciones)).to(self.device).unsqueeze(0)
        with torch.no_grad():
            logits, _ = self.red(x)
            logits = logits_enmascarados(logits, mascara)
            indice = int(torch.argmax(logits, dim=1).item())
        return accion_desde_indice(indice, acciones)

    @classmethod
    def cargar(cls, ruta: Path, device: str = "cpu") -> AgenteRed:
        red = PoliticaValor().to(device)
        red.load_state_dict(torch.load(ruta, map_location=device))
        return cls(red, device)
