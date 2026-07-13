"""La red neuronal: política (qué jugada) + valor (qué tan buena es la posición).

Es una red chica (un tronco compartido con dos cabezas). La política da un puntaje
por cada acción; se **enmascara** para dejar solo las legales antes de elegir.
Este es "el modelo": sus pesos son lo que se aprende (ya no una tabla legible).
"""

from __future__ import annotations

import torch
from torch import nn

from truco.rl.encoder import DIM, N_ACCIONES

_MENOS_INFINITO = -1e9


class PoliticaValor(nn.Module):
    """Actor-crítico: tronco compartido → cabeza de política y cabeza de valor."""

    def __init__(self, dim_entrada: int = DIM, n_acciones: int = N_ACCIONES, oculto: int = 256):
        super().__init__()
        self.tronco = nn.Sequential(
            nn.Linear(dim_entrada, oculto),
            nn.ReLU(),
            nn.Linear(oculto, oculto),
            nn.ReLU(),
        )
        self.cabeza_politica = nn.Linear(oculto, n_acciones)
        self.cabeza_valor = nn.Linear(oculto, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.tronco(x)
        return self.cabeza_politica(h), self.cabeza_valor(h).squeeze(-1)


def logits_enmascarados(logits: torch.Tensor, mascara: torch.Tensor) -> torch.Tensor:
    """Pone -inf en las acciones ilegales para que su probabilidad sea 0."""
    return torch.where(mascara, logits, torch.full_like(logits, _MENOS_INFINITO))
