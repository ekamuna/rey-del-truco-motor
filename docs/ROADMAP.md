# ROADMAP — Rey del Truco (Motor)

Plan por **milestones**. Cada uno es una unidad entendible y jugable/testeable por sí sola. La idea es **ir viendo y entendiendo todo**: no pasás al siguiente hasta que el anterior tiene su "Definición de listo" (DoD) cumplida.

Leyenda: 🎯 objetivo · 🛠️ qué construís · 🧠 qué aprendés · ✅ DoD (listo cuando…)

```
M0 ──▶ M1 ──▶ M2 ──▶ M3 ──▶ M4 ──▶ M5 ──▶ M6 ──▶ (M7 techo)
setup  cartas  motor   jugar   reglas  envido   ML/RL   web/CFR
              bazas   vs bot  +bot v1  +bot v2  self-play
```

---

## 🌱 Fase 0 — El motor (jugar sin IA)

### M0 — Setup del proyecto  ✅ HECHO
- 🎯 Base técnica lista para trabajar con confianza.
- 🛠️ `uv init`, estructura `src/truco/{core,agents,ui}`, `pytest` + `mypy` configurados, `README`, git.
- 🧠 Layout de un proyecto Python serio; por qué los tests van desde el minuto cero.
- ✅ `pytest` corre (aunque sea 1 test trivial) y `mypy` pasa en verde.

### M1 — Cartas y jerarquía  ⭐ *el corazón*  ✅ HECHO
- 🎯 Representar la baraja y el orden de poder REAL del truco.
- 🛠️ `core/cards.py`: `Carta(numero, palo)` + `fuerza_truco(carta) -> int`. `core/mazo.py`: baraja de 40 y reparto.
- 🧠 Que la jerarquía **no es numérica**; las "bravas" (1♠, 1♣, 7♠, 7oro) y las trampas (1 y 7 "falsos" son bajos).
- ✅ `test_jerarquia.py` verifica `1♠ > 1♣ > 7♠ > 7oro > 3 > 2 > 1falso > 12 > 11 > 10 > 7falso > 6 > 5 > 4`, y que dos cartas de igual rango dan **parda**.

### M2 — Motor de la ronda (solo bazas, sin cantos)
- 🎯 Jugar una ronda completa de 3 bazas y saber quién ganó.
- 🛠️ `core/state.py` (`GameState` completo + `ObservableState` por jugador), `core/engine.py` con `legal_actions()`, `step(action)`, `observation_for(jugador)`. Resolución de bazas + desempate por "mano".
- 🧠 Máquina de estados; **la distinción estado completo vs observable** (clave para el ML futuro).
- ✅ Tests: la ronda reparte 2 de 3 bazas correctamente, respeta al "mano" en pardas, y `observation_for` NUNCA revela las cartas del rival.

---

## 🎮 Fase 1 — Jugar contra la máquina (con reglas, sin ML)

### M3 — CLI jugable + agente humano y aleatorio
- 🎯 Poder sentarse y jugar por terminal.
- 🛠️ `agents/base.py` (interfaz `Agent`), `agents/human.py` (lee de CLI), `agents/random.py` (baseline), `game_loop.py`, `ui/cli.py`.
- 🧠 Cómo el mismo loop sirve para cualquier agente; el humano es "un agente más".
- ✅ Un humano juega una ronda completa contra el `RandomAgent` por CLI. (Todavía sin envido.)

### M4 — Truco + `RuleBasedAgent` v1
- 🎯 Un rival que **decide con criterio** en el truco.
- 🛠️ Cantos **Truco / Retruco / Vale Cuatro** con quiero/no-quiero en el engine. `agents/rule_based.py` con heurísticas: clasificar cartas (matas/altas/medias/chicas), cuándo cantar, qué carta guardar, cuándo no querer / ir al mazo. Umbrales parametrizables.
- 🧠 Traducir **estrategia humana a código**; tener una **línea base** medible.
- ✅ El bot guarda las matas para la 2ª/3ª baza, canta truco con manos fuertes, y **le gana holgado al `RandomAgent`** (winrate medido). Ya es divertido jugar contra él.

---

## 🃏 Fase 2 — El juego completo

### M5 — Envido, apuestas completas y partida
- 🎯 Truco "de verdad", partida completa con marcador.
- 🛠️ `core/scoring.py`: cálculo del tanto (20 + 2 cartas del palo), Envido/Real/Falta Envido, regla **"el envido va primero"**. Partida acumulativa a 15/30. `RuleBasedAgent` ampliado con heurísticas de envido y **faroleo** (semi-farol, frecuencia ~20-35%).
- 🧠 Apuestas encadenadas, interacción envido↔truco, por qué el bluff es parte necesaria del juego.
- ✅ Partida a 15 completa humano-vs-bot con envido y truco; el bot cobra el envido bueno y farolea de forma creíble a veces. *(Flor queda detrás de un flag, opcional.)*

---

## 🤖 Fase 3 — Machine Learning (el objetivo de aprendizaje)

### M6 — RL por self-play  ⭐ *acá aprendés ML de verdad*
- 🎯 Un agente que **aprende su estrategia solo**, sin reglas escritas a mano.
- 🛠️ `rl/env.py` (envoltorio Gymnasium `reset()`/`step()`), `rl/encoder.py` (vectoriza `ObservableState` → tensor: one-hot de cartas, flags de cantos, puntos), *action masking* con las acciones legales, `rl/selfplay.py` + `rl/train.py` (PPO o REINFORCE). Arrancar chico: **Q-learning tabular** en una versión reducida antes de las redes. Curriculum: Random → RuleBased → self-play; pool de checkpoints.
- 🧠 Qué significa que una máquina **aprenda de la experiencia**: recompensa sparse (+1/−1), reproducibilidad (semillas), curriculum, evitar el "olvido".
- ✅ El agente entrenado **le gana consistentemente al `RandomAgent`** y compite de igual a igual o mejor contra el `RuleBasedAgent` de M4. *(Esta es la métrica estrella del proyecto.)*

---

## 🏔️ Fase 4 — Techo (opcional, cuando pique el bicho)

### M7 — Web y/o CFR
- 🎯 Pulir y/o llegar al estado del arte.
- 🛠️ **Web:** `ui/web/` con FastAPI, mismo motor detrás. **CFR:** Deep CFR / ISMCTS — la familia que resolvió el póker, específica para info imperfecta + faroleo.
- 🧠 Servir el motor por HTTP; o la matemática del equilibrio en juegos de información imperfecta.
- ✅ Se juega desde el navegador, o el agente CFR supera al de RL. *(No existe bot de truco superhumano público — tierra fértil para investigar.)*

---

## Cómo trabajamos cada milestone
1. Escribimos/actualizamos los **tests primero** cuando aplica (sobre todo en el motor).
2. Implementamos hasta que la **DoD** esté verde.
3. Un commit por milestone con un resumen de qué se aprendió.
4. No saltamos de fase: **el ML (M6) no arranca sin el motor testeado (M0–M5).**
