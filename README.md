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

🛠️ **En construcción** — recorrido completo *de `if/else` a deep learning*: motor testeado → bot de reglas → **opponent modeling** (te lee) → **faroleo** (te miente) → **RL Q-tabular** (aprende las apuestas) → **red neuronal / deep RL** (aprende TODO, incluida la carta). Todos se enchufan a la misma interfaz `Agent`.

**Resultado honesto del panel** (winrate vs estilos agresivo/mentiroso/conservador): el **bot de reglas sigue siendo el mejor** (~61% prom); la **red neuronal** quedó a la par del Q-tabular (~56%) y es la mejor contra rivales conservadores, pero el deep RL ingenuo **no supera** a las reglas escritas a mano. *(Lección real: sofisticación ≠ superioridad; para info imperfecta el techo es CFR, no una red pelada.)*

### Cómo correr
```bash
uv sync                          # entorno (Python 3.12 + torch)
uv run truco                     # jugá vs el bot de reglas (con perfil + faroleo)
uv run truco --usuario emmanuel  # con tu perfil: el bot te va conociendo
uv run truco --rival q           # vs el agente Q tabular (RL)
uv run truco --rival red         # vs la red neuronal (deep RL)
uv run truco-panel               # examen: ¿quién le gana a quién? (tabla de estilos)
uv run truco-entrenar            # entrená el Q tabular
uv run truco-entrenar-red        # entrená la red neuronal
uv run pytest && uv run ruff check . && uv run mypy
```
