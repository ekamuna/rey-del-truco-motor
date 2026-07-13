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

🛠️ **En construcción** — recorrido completo *de `if/else` a la IA de información imperfecta*: motor testeado → bot de reglas → **opponent modeling** (te lee) → **faroleo** (te miente) → **RL Q-tabular** → **red neuronal / deep RL** → **PIMC** (infiere tus cartas ocultas). Todos se enchufan a la misma interfaz `Agent`.

**El campeón del panel** (winrate prom vs azar + estilos agresivo/mentiroso/conservador):

| Agente | Prom | vs Reglas |
|---|---|---|
| **PIMC (infiere)** 🏆 | **~66%** | 60% |
| Bot de reglas | ~63% | — |
| Red (deep RL) | ~57% | 40% |
| Q tabular | ~57% | 39% |

**La lección del proyecto:** en truco **no ganás entrenando más, ganás adivinando mejor lo que no ves.** La red neuronal (770k partidas, millones de pesos) quedó *por debajo* de 50 líneas de `if/else`; el PIMC, que **razona sobre las cartas ocultas** (sin entrenar), es el mejor. El techo real de la información imperfecta es CFR/inferencia, no una red pelada. *(Un oráculo que ve las cartas gana ~90% → esa brecha 66%→90% es el valor de la información oculta.)*

### Cómo correr
```bash
uv sync                          # entorno (Python 3.12 + torch)
uv run truco                     # jugá vs el bot de reglas (con perfil + faroleo)
uv run truco --usuario emmanuel  # con tu perfil: el bot te va conociendo
uv run truco --rival q           # vs el agente Q tabular (RL)
uv run truco --rival red         # vs la red neuronal (deep RL)
uv run truco --rival pimc        # vs el PIMC (te lee / infiere tus cartas) 🏆
uv run truco-panel               # examen: ¿quién le gana a quién? (tabla de estilos)
uv run truco-entrenar            # entrená el Q tabular
uv run truco-entrenar-red        # entrená la red neuronal
uv run pytest && uv run ruff check . && uv run mypy
```
