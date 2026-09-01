# 🃏 Rey del Truco — Engine

A **bot you play Argentine truco against, 1v1, in your terminal**: sit down, it deals
your cards, and you play head-to-head against the machine (envido, truco, bluffs and all).

[English](README.en.md) · [Español](README.md)

You need [**uv**](https://docs.astral.sh/uv/getting-started/installation/) (it manages Python and dependencies for you):

```bash
git clone https://github.com/ekamuna/rey-del-truco-motor.git
cd rey-del-truco-motor
uv sync                          # installs everything the first time (downloads PyTorch, may take a while)
uv run truco --rival pimc        # play the best bot! 🔮
```

Runs **100% locally**: no network, no API keys, no cost. It's a game-theory bot (not a
language model), so playing is free.

## How it plays

You start a 15-point match. Each hand, the bot shows the board, your cards and a menu:

```
  Your cards  (your envido: 27):
     6 de basto
     12 de oro
     1 de basto
  What do you do?
     [0] play the 6 de basto     [3] call ¡TRUCO!
     [1] play the 12 de oro      [4] call ¡ENVIDO!
     [2] play the 1 de basto     ...
```

You pick a number and the bot answers: it calls, accepts, folds, bluffs, or reads you
based on how you've been playing. The **PIMC** — the recommended opponent — *infers your
hidden cards* and plays accordingly.

## Is this machine learning?

Not at first — and that's the point. The project is a walk *from `if/else` to
imperfect-information AI*, with several opponents plugged into the same `Agent` interface:

1. **Rules / heuristics** (not ML) → a solid opponent with opponent modeling and bluffing.
2. **Self-play RL** (this is ML) → tabular Q-learning and a neural net that learn on their own.
3. **PIMC** (Perfect Information Monte Carlo) → reasons about the cards it cannot see.

**Panel champion** (average win rate, 300 matches per pairing, `uv run truco-panel`):

| Agent | Avg | vs Rules | vs bluffers |
|---|---|---|---|
| **PIMC (infers)** 🏆 | **78%** | 78% | 68% / 67% |
| Rule-based bot | 63% | — | 51% / 50% |
| Neural net (deep RL) | 57% | 41% | 50% / 51% |
| Tabular Q | 56% | 39% | 38% / 40% |

**The lesson of the project:** in truco **you don't win by training more, you win by
guessing better at what you can't see.** The neural net (hundreds of thousands of games,
millions of weights) landed *below* the rule-based bot; PIMC, which **reasons about the
hidden cards** without training at all, wins by a wide margin. *(An oracle that saw every
card would win ~90% → that 78%→90% gap is, literally, the value of hidden information.)*
The real ceiling in imperfect information is inference (PIMC / CFR), not a bare network.

## Commands

```bash
uv run truco-web                 # 🌐 play in the BROWSER + tracks your win/loss record
#   └ from your phone (same wifi): uv run truco-web --host 0.0.0.0 → http://<your-computer-ip>:8000
uv run truco --rival pimc        # play in the terminal vs PIMC (it reads / infers your cards) 🏆
uv run truco                     # vs the rule-based bot (opponent modeling + bluffing)
uv run truco --usuario juan      # with your profile: the bot learns you across matches
uv run truco --rival q           # vs the tabular Q agent (RL)
uv run truco-panel               # the exam: who beats whom? (table above)
uv run truco-entrenar            # train tabular Q
```

**ML phase (neural net) and development.** The only part that needs the heavy deps (numpy + PyTorch); playing doesn't. Install the extra:

```bash
uv sync --extra ml               # installs numpy + PyTorch
uv run truco --rival red         # play vs the neural net (deep RL)
uv run truco-entrenar-red        # train the net
uv run pytest && uv run ruff check . && uv run mypy   # full suite (tests + lint + types)
```

## Documentation

The docs are written in Spanish.

| Doc | What for |
|-----|----------|
| [docs/PRD.md](docs/PRD.md) | The *what* and *why*: vision, goals, technical principles |
| [docs/ROADMAP.md](docs/ROADMAP.md) | The *when*: milestones with a "definition of done" |
| [docs/DOCUMENTO-MAESTRO.md](docs/DOCUMENTO-MAESTRO.md) | The *research*: truco rules, AI/ML theory, architecture |
| [docs/CARTA-TRUCO.md](docs/CARTA-TRUCO.md) · [docs/ENVIDO-Y-CANAL.md](docs/ENVIDO-Y-CANAL.md) | The *theory*: exact card and envido equity (truco's "poker chart") |

## Stack

Python 3.11+ · pytest · ruff · mypy (strict) · (ML phase) PyTorch. Managed with `uv`.

## License

[MIT](LICENSE).
