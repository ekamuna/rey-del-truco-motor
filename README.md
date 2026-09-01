# 🃏 Rey del Truco — Motor

Un **bot con el que jugás al truco argentino 1v1 en la terminal**: te sentás, te reparte
las cartas y jugás mano a mano contra la máquina (envido, truco, faroles y todo).

[English](README.en.md) · [Español](README.md)

Necesitás [**uv**](https://docs.astral.sh/uv/getting-started/installation/) (maneja Python y las dependencias por vos):

```bash
git clone https://github.com/ekamuna/rey-del-truco-motor.git
cd rey-del-truco-motor
uv sync                          # instala todo la primera vez (baja PyTorch, puede tardar)
uv run truco --rival pimc        # ¡a jugar contra el mejor bot! 🔮
```

Corre **100% local**: sin conexión, sin claves de API, sin costo. Es un bot de teoría de
juegos (no un modelo de lenguaje), así que jugar no gasta nada.

## Cómo se juega

Arrancás una partida a 15. En cada mano el bot te muestra el tablero, tus cartas y un menú:

```
  Tus cartas  (tu envido: 27):
     6 de basto ♣
     12 de oro ♦
     1 de basto ♣
  ¿Qué hacés?
     [0] jugar el 6 de basto ♣     [3] cantar ¡TRUCO!
     [1] jugar el 12 de oro ♦      [4] cantar ¡ENVIDO!
     [2] jugar el 1 de basto ♣     ...
```

Elegís con el número y el bot responde: canta, quiere, se va al mazo, te farolea o te
lee según cómo venís jugando. El **PIMC** —el rival recomendado— *infiere tus cartas
ocultas* y juega en consecuencia.

## ¿Es machine learning?

No al principio — y esa es la gracia. El proyecto es un recorrido *de `if/else` a la IA
de información imperfecta*, con varios rivales que se enchufan a la misma interfaz `Agent`:

1. **Reglas / heurísticas** (no es ML) → un rival digno con opponent modeling y faroleo.
2. **RL por self-play** (sí es ML) → Q-tabular y una red neuronal que aprenden solas.
3. **PIMC** (Perfect Information Monte Carlo) → razona sobre las cartas que no ve.

**El campeón del panel** (winrate promedio, 300 partidas por cruce, `uv run truco-panel`):

| Agente | Prom | vs Reglas | vs faroleros |
|---|---|---|---|
| **PIMC (infiere)** 🏆 | **78%** | 78% | 68% / 67% |
| Bot de reglas | 63% | — | 51% / 50% |
| Red (deep RL) | 57% | 41% | 50% / 51% |
| Q tabular | 56% | 39% | 38% / 40% |

**La lección del proyecto:** en truco **no ganás entrenando más, ganás adivinando mejor
lo que no ves.** La red neuronal (cientos de miles de partidas, millones de pesos) quedó
*por debajo* del bot de reglas; el PIMC, que **razona sobre las cartas ocultas** sin
entrenar, es el mejor con diferencia. *(Un oráculo que viera las cartas ganaría ~90% → esa
brecha 78%→90% es, literalmente, el valor de la información oculta.)* El techo real de la
información imperfecta es la inferencia (PIMC / CFR), no una red pelada.

## Comandos

```bash
uv run truco --rival pimc        # jugá vs el PIMC (te lee / infiere tus cartas) 🏆
uv run truco                     # vs el bot de reglas (opponent modeling + faroleo)
uv run truco --usuario juan      # con tu perfil: el bot te va conociendo entre partidas
uv run truco --rival q           # vs el agente Q tabular (RL)
uv run truco --rival red         # vs la red neuronal (deep RL)
uv run truco-panel               # el examen: ¿quién le gana a quién? (tabla de arriba)
uv run truco-entrenar            # entrená el Q tabular · truco-entrenar-red para la red
uv run pytest && uv run ruff check . && uv run mypy   # tests + lint + tipos
```

## Documentación

| Doc | Para qué |
|-----|----------|
| [docs/PRD.md](docs/PRD.md) | El *qué* y el *por qué*: visión, objetivos, principios técnicos |
| [docs/ROADMAP.md](docs/ROADMAP.md) | El *cuándo*: milestones con "definición de listo" |
| [docs/DOCUMENTO-MAESTRO.md](docs/DOCUMENTO-MAESTRO.md) | La *investigación*: reglas del truco, teoría de IA/ML, arquitectura |
| [docs/CARTA-TRUCO.md](docs/CARTA-TRUCO.md) · [docs/ENVIDO-Y-CANAL.md](docs/ENVIDO-Y-CANAL.md) | La *teoría*: equity exacta de cartas y envido (la "carta de póker" del truco) |

## Stack

Python 3.11+ · pytest · ruff · mypy · (fase ML) PyTorch. Gestión con `uv`.

## Licencia

[MIT](LICENSE).
