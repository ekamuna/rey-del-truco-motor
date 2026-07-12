# 🃏 Rey del Truco — Motor

El **motor de juego + IA** para jugar al **truco argentino 1v1 contra la máquina**.
Proyecto pensado para construirse por etapas y, de paso, **aprender machine learning** de verdad.

> No confundir con `rey-del-truco-main`, que es el *Anotador de Truco* (app para llevar el puntaje). Esto es otra cosa: el juego y el cerebro del rival.

## La idea en una frase

Un oponente que **sabe cuándo cantar y qué carta jugar** — que empieza como reglas escritas a mano (`if/else`) y evoluciona hasta una IA que **aprende sola** jugando contra sí misma.

## ¿Es machine learning?

No al principio — y esa es la gracia. Se construye en niveles:

1. **Reglas / heurísticas** (no es ML) → un rival digno ya en la Fase 1.
2. **ML / RL por self-play** (sí es ML) → aprende su estrategia, incluido el faroleo.
3. **CFR** (el techo, lo del póker) → info imperfecta óptima.

El bot de reglas es la **línea base**: "¿mi ML le gana a mis `if/else`?" mide el progreso.

## Documentación

| Doc | Para qué |
|-----|----------|
| [docs/PRD.md](docs/PRD.md) | El *qué* y el *por qué*: visión, objetivos, alcance, principios técnicos |
| [docs/ROADMAP.md](docs/ROADMAP.md) | El *cuándo*: milestones M0→M7 con "definición de listo" |
| [docs/DOCUMENTO-MAESTRO.md](docs/DOCUMENTO-MAESTRO.md) | La *investigación*: reglas del truco, teoría de IA/ML, arquitectura |

## Stack

Python 3.11+ · pytest · mypy · (fase ML) PyTorch + Gymnasium · CLI con rich/textual.

## Estado

🛠️ **En construcción** — M0–M5 ✅ + **PerfilDelRival** ✅ + **faroleo** ✅ + **M6 (RL, Q-learning tabular)** ✅. Motor completo, CLI clara, bot de reglas (~91% vs azar), **opponent modeling** (el bot te lee y arma tu fama por usuario), **faroleo**, y un **agente que aprende su estrategia solo** por refuerzo (**96% vs azar** tras entrenar; el "modelo" es una tabla legible). Próximo: refinar el RL (self-play estable / red neuronal).

### Cómo correr
```bash
uv sync                          # crea el entorno (Python 3.12 + deps)
uv run truco                     # jugá vs el bot de reglas (con perfil + faroleo)
uv run truco --usuario emmanuel  # con tu perfil: el bot te va conociendo
uv run truco --rival q           # jugá vs la IA entrenada por refuerzo
uv run truco-entrenar            # entrená el agente Q y mirá subir la curva
uv run pytest                    # tests
uv run ruff check . && uv run mypy   # linter + type-checker
```
