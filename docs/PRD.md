# PRD — Rey del Truco (Motor)

**Producto:** un juego donde una persona juega al **truco argentino 1v1 contra una IA**, con el objetivo doble de (a) tener un juego real y divertido y (b) **aprender machine learning** construyéndolo por etapas.

**Documento hermano:** [DOCUMENTO-MAESTRO.md](DOCUMENTO-MAESTRO.md) (reglas del truco, teoría de IA/ML y arquitectura en detalle).
**Este PRD** define el *qué* y el *por qué*. El [ROADMAP.md](ROADMAP.md) define el *cuándo* (milestones).

---

## 1. Visión

> Un rival de truco que juega bien, que **sabe cuándo cantar y qué carta guardar**, y que puedo hacer cada vez más inteligente — pasando de reglas escritas a mano a una IA que aprende sola.

No es un anotador de puntaje. Esto es el **motor de juego + el cerebro del oponente**.

## 2. Objetivos

| # | Objetivo | Cómo se mide (éxito) |
|---|----------|----------------------|
| O1 | Motor de truco correcto y testeado | La jerarquía, las bazas y el puntaje pasan una suite de tests exhaustiva |
| O2 | Poder jugar contra la máquina | Un humano completa una partida por CLI contra un bot |
| O3 | Oponente que decide con criterio | El bot guarda las matas, cobra el envido bueno, no regala trucos, farolea a veces |
| O4 | **Aprender ML de verdad** | Un agente entrenado por self-play le gana al bot de reglas |
| O5 | Arquitectura que no se reescribe | Cambiar de bot-de-reglas a bot-de-ML = cambiar una línea |

## 3. No-objetivos (por ahora)

- ❌ Multijugador online / 2v2 / 6 jugadores (el 1v1 primero).
- ❌ Señas (no aplican en mano a mano).
- ❌ Gráficos / app móvil nativa (CLI primero; web recién en fase avanzada).
- ❌ Cuentas de usuario, ranking, monetización.
- ❌ Ser un bot "superhumano" (eso es investigación de punta; es el techo, no el piso).

## 4. Usuarios

- **Jugador** — quiere una partida de truco entretenida contra la máquina.
- **Autor/aprendiz (vos)** — quiere entender, tocar y evolucionar cada pieza: el motor, las heurísticas y el ML.

## 5. Alcance funcional (el juego completo, construido por capas)

### Reglas del juego
- Baraja española de 40 cartas, **jerarquía del truco** (no numérica; ver documento maestro).
- Ronda de 3 bazas, "mano" gana desempates, parda.
- **Truco / Retruco / Vale Cuatro** con quiero / no quiero.
- **Envido / Real Envido / Falta Envido**, cálculo del tanto, "el envido va primero".
- Partida acumulativa a 15 (corta) o 30 (larga).
- **Flor: opcional**, detrás de un flag; no entra en la v1.

### El oponente (IA), en niveles
- **v1 — Reglas/heurísticas** (NO es ML): decide con `if/else` y umbrales.
- **v2 — ML/RL por self-play**: aprende su estrategia jugando contra sí mismo.
- (Techo futuro — CFR / ISMCTS, la familia del póker.)

### Interfaz
- **CLI** primero (rich/textual).
- **Web** (FastAPI) como capa opcional que consume el mismo motor, más adelante.

## 6. Requisitos técnicos y principios

- **Stack:** Python 3.11+, pytest, mypy, PyTorch + Gymnasium (fase ML).
- **P1 — Separar reglas de IA:** el motor no sabe *cómo* decide un jugador; la IA no reimplementa reglas.
- **P2 — Estado observable ≠ estado completo:** el `ObservableState` (lo que ve un jugador) se modela desde el día 1; es lo que habilita el RL.
- **P3 — Una sola interfaz `Agent`:** `actuar(obs, acciones) -> Accion`. Sirve igual para reglas y para RL.
- **P4 — `core/` no importa nada de arriba:** dependencias siempre hacia adentro (`ui`/`rl` → `game_loop` → `agents` → `core`).
- **P5 — El motor DEBE tener tests.** Es la base sobre la que se apoya todo el ML.

## 7. Métricas de progreso

- **Cobertura del motor:** % de reglas con test (meta: jerarquía, acciones legales, envido y puntaje al 100%).
- **Winrate del bot** vs `RandomAgent` (debe ser alto ya en v1).
- **Winrate del agente ML** vs `RuleBasedAgent` (la métrica estrella del proyecto: ≥ 50% = el ML aprendió algo real).

## 8. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Modelar mal la jerarquía (1 y 7 "falsos") | Tests primero, específicos para esas trampas |
| Saltar a ML antes de tener motor | El roadmap lo prohíbe: ML recién en M5, con motor testeado |
| Acoplar UI/IA al motor | Regla P4 + revisión de imports |
| Frustración con RL (es lo difícil) | Empezar con Q-learning tabular en versión reducida antes de redes |
