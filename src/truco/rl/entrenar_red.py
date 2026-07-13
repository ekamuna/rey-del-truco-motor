"""Entrenamiento de la red por refuerzo (actor-crítico / REINFORCE con baseline).

El agente (jugador 0) juega rondas contra un **pool de rivales** (azar, reglas,
estilos y copias congeladas de sí mismo). Muestrea sus jugadas de la política,
y al terminar cada ronda ajusta los **pesos** de la red con gradiente para que
las jugadas que llevan a ganar suban de probabilidad. Aprende TODO: qué carta,
qué cantar, cuándo mentir. Nadie le da features ni heurística de carta.
"""

from __future__ import annotations

import copy
import os
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn, optim

from truco.agents.aleatorio import AgenteAleatorio
from truco.agents.base import Agent
from truco.agents.estilos import agresivo, conservador, mentiroso
from truco.agents.reglas import AgenteReglas
from truco.core.engine import acciones_legales, actor, aplicar, nueva_ronda, observacion_de
from truco.evaluacion import enfrentar
from truco.rl.agente_red import AgenteRed
from truco.rl.encoder import accion_desde_indice, codificar, mascara_legal
from truco.rl.red import PoliticaValor, logits_enmascarados

_RUTA_MODELO = Path("modelos/red.pt")


def _rollout(
    red: PoliticaValor, rival: Agent, device: str, rng: random.Random, mano: int
) -> tuple[list[np.ndarray], list[np.ndarray], list[int], float]:
    """Juega una ronda (aprendiz=0 muestrea de la política, rival juega) y la registra."""
    estado = nueva_ronda(seed=rng.randrange(2**31), mano=mano)
    xs: list[np.ndarray] = []
    ms: list[np.ndarray] = []
    idxs: list[int] = []
    while not estado.terminada:
        jugador = actor(estado)
        obs = observacion_de(estado, jugador)
        concretas = acciones_legales(estado)
        if jugador == 0:
            x = codificar(obs)
            m = mascara_legal(concretas)
            xt = torch.from_numpy(x).unsqueeze(0).to(device)
            mt = torch.from_numpy(m).unsqueeze(0).to(device)
            with torch.no_grad():
                logits, _ = red(xt)
                probs = torch.softmax(logits_enmascarados(logits, mt), dim=1)
                indice = int(torch.multinomial(probs, 1).item())
            xs.append(x)
            ms.append(m)
            idxs.append(indice)
            accion = accion_desde_indice(indice, concretas)
        else:
            accion = rival.actuar(obs, concretas)
        estado = aplicar(estado, accion)

    diff = estado.puntos_ronda[0] - estado.puntos_ronda[1]
    recompensa = float((diff > 0) - (diff < 0))
    return xs, ms, idxs, recompensa


def entrenar_red(
    iteraciones: int = 3000,
    batch: int = 64,
    lr: float = 1e-3,
    coef_valor: float = 0.5,
    coef_entropia: float = 0.01,
    coef_entropia_final: float | None = None,
    device: str = "cpu",
    seed: int = 0,
    eval_cada: int = 100,
    eval_partidas: int = 200,
    checkpoint: Path | None = _RUTA_MODELO,
    cada_self_play: int = 150,
) -> tuple[PoliticaValor, list[tuple[int, float]]]:
    """Entrena la red. Devuelve (red, curva de winrate vs Aleatorio)."""
    torch.manual_seed(seed)
    torch.set_num_threads(max(1, (os.cpu_count() or 2)))
    red = PoliticaValor().to(device)
    optimizador = optim.Adam(red.parameters(), lr=lr)
    rng = random.Random(seed)

    pool: list[Agent] = [
        AgenteAleatorio(seed=1),
        AgenteReglas(),
        agresivo(2),
        mentiroso(3),
        conservador(4),
    ]
    curva: list[tuple[int, float]] = []

    for it in range(iteraciones):
        red.train()
        xs_b: list[np.ndarray] = []
        ms_b: list[np.ndarray] = []
        idx_b: list[int] = []
        ret_b: list[float] = []
        for b in range(batch):
            rival = rng.choice(pool)
            xs, ms, idxs, recompensa = _rollout(red, rival, device, rng, mano=b % 2)
            xs_b.extend(xs)
            ms_b.extend(ms)
            idx_b.extend(idxs)
            ret_b.extend([recompensa] * len(xs))

        if not xs_b:
            continue

        X = torch.from_numpy(np.stack(xs_b)).to(device)
        M = torch.from_numpy(np.stack(ms_b)).to(device)
        A = torch.tensor(idx_b, dtype=torch.long, device=device)
        G = torch.tensor(ret_b, dtype=torch.float32, device=device)

        logits, valores = red(X)
        logits = logits_enmascarados(logits, M)
        logprobs = torch.log_softmax(logits, dim=1)
        logp_accion = logprobs.gather(1, A.unsqueeze(1)).squeeze(1)

        ventaja = G - valores.detach()
        perdida_politica = -(logp_accion * ventaja).mean()
        perdida_valor = nn.functional.mse_loss(valores, G)
        probs = torch.softmax(logits, dim=1)
        entropia = -(probs * logprobs.clamp_min(-50)).sum(dim=1).mean()
        ce = coef_entropia
        if coef_entropia_final is not None:
            ce = coef_entropia + (coef_entropia_final - coef_entropia) * (it / iteraciones)
        perdida = perdida_politica + coef_valor * perdida_valor - ce * entropia

        optimizador.zero_grad()
        perdida.backward()
        nn.utils.clip_grad_norm_(red.parameters(), 1.0)
        optimizador.step()

        # Sumar una copia congelada de la red actual al pool (self-play con historia).
        if it > 0 and it % cada_self_play == 0:
            congelada = PoliticaValor().to(device)
            congelada.load_state_dict(copy.deepcopy(red.state_dict()))
            pool.append(AgenteRed(congelada, device))

        if eval_cada and it % eval_cada == 0:
            wr = _winrate(red, device, eval_partidas)
            curva.append((it, wr))
            if checkpoint is not None:
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                torch.save(red.state_dict(), checkpoint)

    if checkpoint is not None:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save(red.state_dict(), checkpoint)
    return red, curva


def _winrate(red: PoliticaValor, device: str, partidas: int) -> float:
    return enfrentar(
        lambda: AgenteRed(red, device),
        lambda: AgenteAleatorio(seed=1),
        partidas=partidas,
        seed=12345,
    ).winrate_a


def main() -> None:
    """Comando de consola: entrena la red y guarda los pesos."""
    import argparse

    parser = argparse.ArgumentParser(description="Entrenar la red de truco (deep RL).")
    parser.add_argument("--iteraciones", type=int, default=3000)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--salida", default=str(_RUTA_MODELO))
    args = parser.parse_args()

    print(f"Entrenando la red: {args.iteraciones} iteraciones x {args.batch} rondas…\n")
    red, curva = entrenar_red(
        iteraciones=args.iteraciones, batch=args.batch, checkpoint=Path(args.salida)
    )
    for it, wr in curva:
        print(f"  iter {it:>5}:  {wr:5.0%}  " + "█" * int(wr * 40))
    print(f"\nRed guardada en {args.salida}")
