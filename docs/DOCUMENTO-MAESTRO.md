# Rey del Truco — Documento Maestro

*Guía de referencia para aprender el juego y construir el bot, paso a paso.*

> **Nota:** documento conceptual. Los nombres de archivo/función y el árbol de carpetas son ilustrativos; el código real usa nombres en español (ver `src/truco/`). La interfaz real de un agente es `actuar(obs, acciones)`.

---

## 1. Qué es el truco argentino

El truco es un juego de cartas de **información incompleta, apuestas y engaño**. No gana el que tiene las mejores cartas, sino el que mejor administra lo que tiene y lo que el rival cree que tiene. Es, en esencia, un "póker criollo".

### El mazo
Baraja española de **40 cartas**, cuatro palos (espada, basto, oro, copa). Se juega con 1, 2, 3, 4, 5, 6, 7, 10 (sota), 11 (caballo) y 12 (rey). **No hay 8 ni 9 ni comodines.**

### Jerarquía de poder (¡NO es el orden numérico!)
Cuatro cartas únicas mandan en la cima ("las bravas"), y abajo el orden se altera:

1. **1 de espada** (la más fuerte, "el macho")
2. **1 de basto**
3. **7 de espada**
4. **7 de oro**
5. Los **3** — 6. Los **2** — 7. **1 de oro / 1 de copa** (los "anchos falsos", ¡son bajos!) — 8. Reyes (12) — 9. Caballos (11) — 10. Sotas (10) — 11. **7 de copa / 7 de basto** (los "sietes falsos", bajos) — 12. Los 6 — 13. Los 5 — 14. Los 4.

> **Los dos errores clásicos al programar:** el 1 de oro/copa NO es alto (apenas supera al rey), y el 7 de copa/basto es débil (por debajo de la sota). Solo espada/basto (anchos) y espada/oro (sietes) son las bravas.

Cuando se enfrentan dos cartas del mismo rango, la mano es **parda** (empate).

### La ronda
Se reparten **3 cartas** a cada uno. Se disputan hasta **3 manos (bazas)**: en cada una, cada jugador tira una carta y gana la de mayor jerarquía. **Gana la ronda quien se lleva 2 de 3 manos.** En empates generales, gana **el "mano"** (el que juega primero). Ser mano es una ventaja estructural enorme: define los desempates.

### El envido (fase de apuesta 1, solo en la primera mano)
Se apuesta por el **tanto**: dos cartas del mismo palo suman `20 + sus valores` (figuras = 0); sin par de palo, vale la carta más alta. Mínimo 0, **máximo 33**.
- **Envido** = 2 · **Real Envido** = 3 · **Falta Envido** = lo que le falta al puntero para ganar la partida.
- Se acumulan y encadenan; al "no quiero" se paga el valor previo (mín. 1).
- En empate de tanto, gana **el mano**. Y una regla de oro: **"el envido va primero"** (si se cantan envido y truco juntos, el envido se resuelve antes).

### El truco (fase de apuesta 2)
Escalera de tres niveles sobre el valor de la ronda:
- **Truco** = 2 · **Retruco** = 3 · **Vale Cuatro** = 4 (tope).
- Se sube de a un escalón. Al "no quiero" se paga el nivel anterior (1/2/3). Al "quiero", el ganador de las bazas se lleva el valor del nivel.

### La partida
Acumulativa hasta llegar a **30 puntos** (larga, dividida en "malas" 0-15 y "buenas" 15-30) o **15** (corta). Cada ronda suma envido + truco al marcador.

*(La **flor** —3 cartas del mismo palo— es una variante opcional. Para la primera versión, se omite por completo.)*

---

## 2. ¿El oponente IA es "machine learning"? (el corazón del documento)

**Respuesta honesta: no necesariamente.** "IA" es el paraguas; "machine learning" es una habitación adentro de ese paraguas. Podés tener una IA que juegue al truco muy dignamente **sin una sola línea de ML**. Hay tres niveles, de menos a más:

### Nivel 1 — Reglas / heurísticas → **NO es ML**
Programás el conocimiento de un buen jugador como `if/else`, tablas y fórmulas. Vos escribís las reglas; la máquina las ejecuta.

```
puntos = calcular_envido(mis_cartas)
if puntos >= 28:          cantar("envido")
elif puntos >= 25 and soy_mano:  cantar("envido")
else:                     no_cantar()
```

- **Ventajas:** funciona YA, sin datos ni GPU. Es **interpretable** (si juega mal, abrís el código y ves por qué). Es lo que usan casi todos los juegos comerciales de cartas.
- **Límites:** es tan bueno como las reglas que sepas escribir; el faroleo fino es difícil de codear a mano.

### Nivel 2 — Búsqueda (MCTS + determinización) → es IA, **no es ML**
La máquina no aprende: **simula el futuro** y elige la jugada con mejor promedio. Como no ve las cartas del rival, "imagina" muchos repartos posibles (determinización), resuelve cada uno como información perfecta y promedia. **No necesita datos ni entrenamiento**, sí cómputo al decidir. Su límite: **subestima el bluff**, porque asume que todos juegan a cartas vistas.

### Nivel 3 — Machine Learning de verdad
El sistema **aprende la estrategia solo**, sin que vos escribas las reglas:
- **RL / self-play (tipo AlphaZero):** juega millones de partidas contra sí mismo, recibe recompensa (+1 gana / −1 pierde) y una red neuronal ajusta sus decisiones. **No hace falta dataset humano** — los datos los genera el propio juego. El faroleo *emerge* solo.
- **CFR (Counterfactual Regret Minimization):** el algoritmo que resolvió el póker (Libratus, Pluribus). Está diseñado *específicamente* para información imperfecta con faroleo — es decir, exactamente la naturaleza del truco. Es lo técnicamente más apropiado... y lo más difícil.

| Enfoque | ¿Es ML? | ¿Datos? | ¿GPU? | Dificultad | ¿Modela el bluff? |
|---|---|---|---|---|---|
| Reglas / heurísticas | No | No | No | Baja | A mano, pobre |
| Búsqueda (MCTS) | No | No | Sí, al decidir | Media | Flojo |
| RL / self-play | Sí | No (self-play) | Sí, mucho | Media-alta | Sí, emergente |
| CFR | Sí | No (self-play) | Sí | Alta | Sí, es su especialidad |

### La recomendación clave: EMPEZÁ POR REGLAS, evolucioná hacia ML
No arranques por lo sofisticado. Un bot de reglas te da un juego jugable **este fin de semana** y te construye la infraestructura (motor + rival base) sobre la que después montás el ML de verdad. Además:
- **Sin motor de juego no podés hacer nada de ML:** RL y CFR necesitan un simulador donde jugar.
- **Tu bot de reglas será tu línea base:** "¿mi ML le gana a mis if/else?" es la pregunta que mide tu progreso.

Cada paso reutiliza el anterior. Empezás por reglas, seguís por RL. Ese es el camino.

---

## 3. Cómo "piensa" un buen jugador (la base del primer bot)

El buen jugador optimiza tres cosas a la vez: **el valor de sus cartas**, **el valor de la apuesta** (puntos en juego + marcador) y **el valor de la información** (lo que revela y lo que infiere). Estas heurísticas son exactamente lo que vas a codear en el `RuleBasedAgent`.

### Clasificá cada carta
- **Matas/bravas** (1 espada, 1 basto, 7 espada, 7 oro): ganan casi cualquier baza. Se guardan y administran.
- **Altas** (3, 2): ganan la mayoría.
- **Medias** (1 falso, 12, 11, 10): sirven para envido, débiles para truco.
- **Chicas** (7 falso, 6, 5, 4): casi solo para envido o para "tirar".

### Envido: cuándo cantar
- `≥ 27` → cantá. `≥ 29` → escalá a real/falta envido (casi ganado).
- `25-26` → cantá simple, no escales.
- `≤ 20` → solo como farol o para "medir" al rival.
- Como **pie**, exigite ~+2 puntos al umbral. Si el mano NO cantó teniéndolo, asumí que su envido es bajo.

### Truco: cuándo cantar
- Con **dos cartas ganadoras** (dos matas, o mata + 3) → cantá.
- Con **una mata + carta media, siendo mano** → cantá (la mata asegura una baza, la ventaja de mano define pardas).
- **Después de ganar la primera baza** → cantá: es el mejor momento, por valor o por farol.

### Administración de cartas (qué guardar)
- **Guardá el 1 de espada / las matas** para la 2ª o 3ª baza, que es donde se define. Excepción: tirala primera si necesitás la iniciativa.
- Siendo **mano** con mata + media, buscá **pardar la primera** con la media: si empatás, con ganar cualquiera de las siguientes te llevás la ronda.
- Como **pie**, ganá cada baza con la **carta mínima suficiente**; reservá las altas.
- **No reveles** cartas altas ni el palo del envido si no hace falta. Cada carta jugada le dice al rival qué te queda.

### Farolear (el bluff no es opcional)
- Preferí el **semi-farol** (cantar truco con una mata sola): si te quieren, todavía podés ganar.
- Un farol es creíble **después de ganar una baza** o de mostrar envido: el rival infiere cartas altas.
- Frecuencia de farol ~20-35%, ajustada al rival. **Si te quieren seguido, dejá de farolear** y castigá con manos reales.

### No querer / irse al mazo
- Si tu probabilidad de ganar es baja (< ~35-40%) y el costo es chico → no quieras.
- Tres cartas chicas sin envido cobrable → **al mazo** (perdés 1, salvás el marcador).

### El marcador cambia TODO
- **Perdiendo por mucho** → bajá umbrales, farolá más, buscá falta envido / vale cuatro (necesitás varianza).
- **Ganando por mucho** → subí umbrales, menos farol (querés baja varianza para cerrar).
- **Rival a 1-2 de ganar** → endurecé: no le regales trucos ganables, no farolees a lo loco.

> **Nota sobre 1v1:** las señas son comunicación entre compañeros de equipo. En mano a mano **no existen ni aplican**. Ignoralas por completo.

---

## 4. Arquitectura y stack recomendados

### Principios rectores
1. **Separá reglas de la IA.** El motor no sabe "cómo decide" un jugador; la IA no reimplementa reglas.
2. **Una sola interfaz de Agente**, que sirva igual para un bot de reglas hoy y un agente de RL mañana.
3. **El estado observable ≠ el estado completo.** El truco tiene información oculta. Modelar esto desde el día 1 es lo que habilita el RL después.
4. **Empezá por CLI.** La web es una capa que consume el mismo motor.

### Stack: **Python**
Es el ecosistema dominante de ML/RL (PyTorch, NumPy, Gymnasium), permite prototipar rápido y conecta el motor directo al loop de entrenamiento. Es lento, pero para truco 1v1 no importa (el árbol es chico).

```
Lenguaje  : Python 3.11+          Tests : pytest (el motor DEBE tener tests)
Tipado    : type hints + mypy     ML/RL : PyTorch + Gymnasium
CLI       : rich / textual        Web   : FastAPI (fase 3, mismo motor)
```

### Los cuatro módulos
- **(a) Motor de reglas** (`core/`): máquina de estados pura. Reparte, valida acciones, resuelve envido/truco, cuenta puntos, expone acciones legales. **Sin I/O, sin ML** → 100% testeable.
- **(b) Representación del estado:** dos objetos distintos, la distinción más importante del proyecto:
  - `GameState` (completo, con ambas manos) — vive en el motor, **nunca** se le da a un agente.
  - `ObservableState` (por jugador) — solo lo que ESE jugador puede ver. Es lo que recibe el agente y lo que después vectorizás a un tensor. Esta proyección garantiza el "fog of war" del juego de información imperfecta.
- **(c) Agente** (`agents/`): una interfaz común, muchas implementaciones (Random, RuleBased, Human, RL).
- **(d) UI** (`ui/`): CLI en fase 1, web en fase 3. El humano es literalmente un `HumanAgent`.

### La interfaz del Agente (la decisión clave)
Una única firma que funciona para reglas y para RL:

```python
class Agent(ABC):
    @abstractmethod
    def act(self, obs: ObservableState, legal_actions: list[Action]) -> Action: ...
    def observe_result(self, reward: float, done: bool) -> None: pass  # solo RL lo usa
```

- **Input = estado observable + acciones legales.** Pasar las acciones legales explícitamente evita que cada agente reimplemente las reglas. El bot de reglas elige con heurísticas; el de RL enmascara los logits ilegales. Ambos usan lo mismo.
- **Output = una `Action`** de un espacio **discreto y de tamaño fijo** (jugar carta 0/1/2, cantar envido/truco/etc., quiero, no quiero, mazo). Definirlo una sola vez es lo que permite mapear la salida de la red sin tocar el motor.

Con esto, el loop del juego es **idéntico** para cualquier agente. Cambiar de bot de reglas a bot de RL es cambiar una línea: `agents[1] = RLAgent(policy)`.

### Estructura de carpetas
```
rey-del-truco/
├── src/truco/
│   ├── core/       # (a) MOTOR — cards, actions, state, engine, scoring, rng
│   ├── agents/     # (c) AGENTES — base(ABC), random, rule_based, human, rl_agent
│   ├── rl/         # entrenamiento (fase 3) — env(Gym), encoder, selfplay, train
│   ├── ui/         # (d) cli.py ; web/ (FastAPI)
│   └── game_loop.py
├── tests/          # el MOTOR debe tener tests exhaustivos
├── logs/           # partidas en JSON para replay
└── checkpoints/    # políticas entrenadas
```

**Regla estricta de dependencias:** `core/` no importa NADA de arriba. `ui/` y `rl/` → `game_loop` → `agents/` → `core/`. Si `core/` alguna vez necesita importar de `ui/` o `rl/`, algo está mal diseñado.

---

## 5. Roadmap de aprendizaje por fases

### Fase 0 — Motor del juego (reglas base, sin envido/flor)
- **Qué construís:** cartas + jerarquía del truco (`core/cards.py`), `GameState`/`ObservableState` con su proyección, `engine.py` con `step()` / `legal_actions()` / `observation_for()`, y el reparto y resolución de las 3 bazas. Truco/retruco/vale cuatro sí; envido y flor todavía no. Un `HumanAgent` que lee de la CLI.
- **Qué aprendés:** máquinas de estados, la sutileza de la jerarquía (que NO es numérica), y la distinción estado completo vs observable — la base conceptual de todo el proyecto.
- **Listo cuando:** dos humanos pueden jugar una partida completa por CLI, con tests que cubren la jerarquía, las acciones legales y el flujo de una mano.

### Fase 1 — Bot de reglas/heurísticas (NO ML) — ya jugás contra la máquina
- **Qué construís:** `RandomAgent` (baseline) y `RuleBasedAgent` con las heurísticas de la sección 3 (cuándo cantar truco, qué carta guardar, cuándo ir al mazo), umbrales parametrizables.
- **Qué aprendés:** a traducir estrategia humana en código, y a tener tu **línea base** contra la cual medir todo el ML futuro.
- **Listo cuando:** un humano juega contra el bot por CLI y el bot toma decisiones razonables (guarda las matas, cobra el envido bueno, no regala trucos). **Ya tenés un juego real y divertido.**

### Fase 2 — Envido y apuestas completas
- **Qué construís:** `scoring.py` con el cálculo del tanto (20 + dos cartas del mismo palo), envido/real/falta envido, la regla "el envido va primero", y la escalera completa del truco con sus "quiero/no quiero". Ampliás el `RuleBasedAgent` con las heurísticas de envido y bluff.
- **Qué aprendés:** el sistema de apuestas encadenadas, la interacción envido↔truco, y por qué el faroleo es parte necesaria del juego (no un adorno).
- **Listo cuando:** se juega una partida a 15 completa, con envido y truco, marcador acumulativo, y el bot farolea de vez en cuando de forma creíble.

### Fase 3 — ML/RL por self-play — acá aprendés machine learning de verdad
- **Qué construís:** un envoltorio `TrucoEnv` (API Gymnasium `reset()`/`step()`), un `encoder` que vectoriza el `ObservableState` a un `np.ndarray` (one-hot de cartas, flags de cantos, puntos), *action masking* con las acciones legales, y el loop de **self-play** (`selfplay.py` + `train.py`) con PPO o REINFORCE. Empezá chico: Q-learning tabular en una versión reducida antes de saltar a redes.
- **Qué aprendés:** qué significa realmente que una máquina aprenda de la experiencia; recompensa (sparse: +1/−1), reproducibilidad (logs con semilla), curriculum (Random → RuleBased → self-play) y pool de oponentes (jugar contra checkpoints viejos para no "olvidar").
- **Listo cuando:** tu agente entrenado le gana consistentemente al `RandomAgent` y compite de igual a igual (o mejor) contra tu `RuleBasedAgent` de la Fase 1.

> **El techo, no el piso:** para juego óptimo de verdad con faroleo calibrado, la familia correcta es **CFR / Deep CFR / ISMCTS** (la del póker). Es investigación de punta aplicada al truco — tierra fértil, porque no existe un bot superhumano de truco público. Dejalo para cuando domines todo lo anterior y te pique el bicho.

---

## 6. Próximo paso concreto: qué hacer HOY

1. **Creá el proyecto:** `uv init rey-del-truco` (o poetry), con `pytest` y `mypy` configurados.
2. **Modelá `core/cards.py`:** una clase `Carta` (número + palo) y una función de **jerarquía del truco** que devuelva la fuerza de cada carta. Es la base y es sorprendentemente sutil.
3. **Escribí los tests primero:** `test_jerarquia_cartas.py` que verifique que 1 espada > 1 basto > 7 espada > 7 oro > los 3 > ... y que el 1 de oro y el 7 de basto son **bajos**. Si esto pasa, tenés el corazón del motor bien puesto.

Con eso arrancado, la Fase 0 se completa sola en unos días. No toques ML hasta la Fase 3 — el ML se **enchufa** encima gracias a la interfaz `Agent`, sin reescribir nada. Dale para adelante.
