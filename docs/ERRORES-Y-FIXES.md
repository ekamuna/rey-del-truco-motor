# Errores del bot y cambios a hacer (de la tanda 2–1 con ground-truth)

> Análisis con **verdad de fondo** (cartas ocultas del bot + cada decisión, replay
> instrumentado `scratchpad/analizar_tanda.py`). Se listan **sólo los puntos que
> PERDIÓ el bot**, marcados ❌ (perdió mal = error corregible) o ✅ (perdió bien =
> fold correcto o cartas peores, inevitable). Foco del usuario: el bot debe ser
> **CONSERVADOR** (no farolear). Muchos de mis puntos fueron **cartas (suerte)**;
> acá sólo interesa dónde el bot **regaló** puntos.

## Enumeración completa de puntos perdidos por el bot

### Partido 3
| Ronda | Concedió | Mecanismo | Veredicto |
|---|---|---|---|
| R1 | 1 envido | foldeó 26 (pie) vs mi canto de mano con 29 (yo iba mejor) | ✅ fold correcto |
| R1 | 2 truco | **cantó truco con 7o(10)+6c(2)+12c(6)** (una carta buena + basura); ganó baza1 pero perdió 2&3; yo tenía 7e(11) | ❌ **cant flojo de truco** (1 carta + basura) — convirtió un −1 en −2 |
| R2 | 2 envido | **cantó envido DE MANO con 24**, lo quise con 30 | ❌ **envido ofensivo flojo** (canta 24 de mano) |
| R2 | 1 truco | sin cantar; mano basura (4e,12e,12b), perdió la mano | ✅ inevitable (cartas malas) |
| R3 | 1 envido | foldeó 4 vs mi canto de mano 23 | ✅ fold correcto |
| R4 | 2 envido | cantó envido de mano con 26, lo quise con 31 | ✅ borderline (26 de mano es razonable, cayó ante mejor tanto) |
| R7 | **4 truco** | **subió a VALE CUATRO con 3c(9)+10e(4)+6c(2)** (basura) porque leyó mi slow-play como debilidad; yo tenía macho+hembra | ❌❌ **EL PEOR: farol de vale4 sin nada** |

### Partido 4
| Ronda | Concedió | Mecanismo | Veredicto |
|---|---|---|---|
| R1 | 2 envido | **cantó envido DE MANO con 23**, lo quise con 26 | ❌ **envido ofensivo flojo** (canta 23 de mano) |
| R2 | 1 envido | foldeó 25 vs mi canto de mano 32 | ✅ fold correcto |
| R3 | 1 envido | foldeó 7 vs mi 29 | ✅ fold correcto |
| R5 | 1 truco | lideró 4o(0) de mano, perdió la mano ante mi 3e(9) | ✅ inevitable (mi 3e era la mejor) |
| R6 | 1 envido | **foldeó 26 (pie) vs mi canto de mano 23 — ¡tenía el mejor tanto y se achicó!** | ❌ **over-fold de envido** (folea un 26 ganador) |
| R6 | 2 truco | **cantó truco con hembra(12)+6o(2)+10o(4)** (monstruo + basura); ganó baza1 con la hembra, perdió 2&3 | ❌ **cant flojo de truco** (1 monstruo + basura) |
| R7 | 1 envido | foldeó 3 vs mi 27 (tenía macho+3b+2c, mano real de truco) | ✅ fold correcto |
| R9 | 1 truco | foldeó mi truco con mano basura (11e,5c,11b) estando yo 1-0 | ✅ fold correcto |
| R10 | 1 envido | foldeó 6 vs mi 27 | ✅ fold correcto |
| R10 | 1 truco | sin cantar; basura total (5e,6o,5c), perdió 2-0 | ✅ inevitable |
| R11 | 1 truco | foldeó mi truco con basura (7c,10o) estando yo 1-0 | ✅ fold correcto |
| R13 | 1 envido | foldeó 7 vs mi 21 (tenía macho+7o, monstruo) | ✅ fold correcto |
| R14 | 1 envido | **foldeó 26 (pie) vs mi canto de mano 23 — otra vez el mejor tanto se achicó, y con esto perdí... perdió la partida (yo llegué a 15)** | ❌ **over-fold de envido (le costó la partida)** |
| R14 | 1 truco | foldeó mi truco con basura (5b,6o,11o) | ✅ fold correcto |

### Partido 5 (lo ganó el bot, pero igual regaló estos)
| Ronda | Concedió | Mecanismo | Veredicto |
|---|---|---|---|
| R3 | 2 truco | **cantó truco (estando 1-0) con 12b(6)+10o(4)+6o(2)** (carta baja + basura); yo tenía 2c(8)+3o(9) | ❌ **cant de truco con carta baja** desde posición que no aguantaba |
| R6 | 2 truco | **lideró 4b(0) de mano** (regaló baza1 y el desempate) y después **quiso mi truco desde 0-1** con 3c+12e; perdió la mano en la parda de la 3ª (yo había hecho primera) | ❌ **no hizo primera** (lideró basura de mano) + quiso flojo |
| R7 | 1 envido | foldeó 6 vs mi 22 | ✅ fold correcto |
| R7 | 1 truco | foldeó mi truco con basura (6e,5c,4o) | ✅ fold correcto |

## Resumen de errores (dónde perdió MAL) — agrupados

**Total regalado por error ≈ 15-16 puntos en la tanda.** Cuatro cubos:

1. ❌❌ **Ofensiva de truco farolera / sobre-agresiva** (P3-R1, **P3-R7**, P4-R6, P5-R3) — **~9 pts, el bleed #1.**
   El bot **canta y escala el truco con "una carta + basura" o directamente con basura**. El caso extremo: **vale-cuatro con un 3(9) porque me leyó débil** (P3-R7). Esto es exactamente "farolear sin nada" — lo OPUESTO a conservador. El PIMC sobreestima su prob de ganar cuando el rival hace slow-play y escala a ciegas.

2. ❌ **Defensa de envido demasiado miedosa (over-fold)** (P4-R6, **P4-R14**) — **folea 26 ganadores.**
   Asume que "el mano que canta tiene puntos" y **foldea un 26 (que gana) contra mi canto de mano con 23**. Contra un rival que **canta envido seguido/liviano** (yo cantaba todas las manos), foldear el 26 es una fuga enorme. **Le costó la partida 2 del... la ronda 14.** Es el **Target #1**.

3. ❌ **Ofensiva de envido floja** (P3-R2, P4-R1) — **canta envido de mano con 23-24.**
   Justo tu ejemplo ("le gané, tenía 22-23"). Canta de mano con tanto flojo y cae ante un tanto mayor. Un bot conservador canta de mano sólo con tanto fuerte.

4. ❌ **No hace primera / lidera basura de mano** (P5-R6) — regala baza1 y el desempate de parda con mano mediocre.

**Todo lo demás que perdió lo perdió BIEN** ✅: foldeó envidos cuando iba realmente atrás (4,5,7,3,6), foldeó trucos con basura estando yo 1-0, y perdió manos donde yo tenía cartas mejores (mi hembra, mi 7e vs su 7o, mi 3e). Eso NO se toca — es correcto.

## Cambios a hacerle al bot (en orden de impacto)

### FIX A — Ofensiva de truco CONSERVADORA (bleed #1, ~9 pts)
- **Nunca escalar (retruco/vale4) como farol.** Escalar el truco sólo con holding top real (tiene una brava, o va 2-0 en bazas), **ignorando** la prob del PIMC cuando ésta viene inflada por un rival que hizo slow-play. Regla dura anti-farol.
- **No cantar truco con "1 carta + basura".** Exigir ≥2 ganadores plausibles de baza, o posición real (2-0, o 1-0 con una segunda carta de verdad). Un 7o/hembra solos no alcanzan si el resto es basura.
- Es el fix más alineado con "el bot conservador": corta el vale4-con-3 y compañía.

### FIX B — Defensa de envido por FRECUENCIA de canto (Target #1, cost. una partida)
- Contar la **frecuencia con que el rival canta envido** (no sólo los faroles destapados). Si canta seguido → **ensanchar el rango de quiero**: pagar con 26+ (incluso 24) en vez de foldear.
- Arregla el "folea un 26 ganador" (P4-R6, R14). Es corrección, no agresión.

### FIX C — Ofensiva de envido conservadora
- Cantar envido **de mano** sólo con tanto fuerte (usar umbral de equity real; no cantar 23-24 de mano). Reduce las pérdidas de showdown por canto flojo.

### FIX D — Hacer primera con mano mediocre
- De mano con mano floja/mediocre, **ganar la primera** (asegurar el desempate de parda) en vez de liderar la basura. Revisar por qué la política de liderazgo no lo aplicó en P5-R6.

## Protocolo (docs/NORTE.md)
Cada fix: commit revertible, TDD + ruff + mypy, y **medir contra el panel completo** (winrate + dif. de puntos, partidos no manos) para confirmar que no rompe nada. Rivales de test: `farolero_envido_real` (FIX B), y un rival que quiera trucos para castigar los farols del bot (FIX A).

---

## FIX F — Quiero de truco consciente del marcador (muerte súbita)

**Corroborado jugando 3 partidos derecho (seeds 33/42/99, harness `scratchpad/jugar_normal.py`; ground-truth `scratchpad/analizar_normal.py`). Récord humano 2 – bot 1.**

**El leak (g1 ronda 11 sutil, g2 ronda 13 clarísimo):** el quiero de truco usaba el break-even de puntos PURO (0.25) e ignoraba el marcador. Yendo **14-13**, con una mano SIN fuertes (12,12,6 → máx f6, ~25%), el bot quiso mi truco porque `0.25 ≥ 0.25` y **me regaló el partido**. Foldeando quedaba 14-14 (~50%).

**El arreglo (`pimc.py::_umbral_querer_truco_ev`, análoga a FIX E):** cerca del final el punto no es lineal. Si perder el quiero le da el PARTIDO al rival (`opp + V ≥ objetivo`) pero foldear lo mantiene vivo (`opp + Pnq < objetivo`) **y no va atrás**, el quiero es *muerte súbita* → exige ser **favorito (0.5)**, no el break-even. Si foldear también pierde, o si va atrás, break-even normal (pelea, necesita la varianza).

- Panel A/B **NEUTRO** (75.2% → 75.3%, seeds 11/22/33 × 120): sólo cambia la zona de muerte súbita, rara en el panel, pero evita regalar partidos ganados.
- TDD (`test_umbral_querer_truco_sube_a_favorito_en_muerte_subita`), 158 tests, mypy strict. Commit `84a7779`.

**Partido 3: el bot jugó impecable, cero errores nuevos.** Nunca faroleó (aperturas con 2-3 fuertes reales), foldeó trucos perdidos, cantó de valor en la baza decisiva con cartas fuertes, envido agresivo+correcto, y **endgame perfecto (a 14-11 abrió truco con dos 3 y cerró el partido)** — justo lo que FIX F protege del lado contrario. Ganó por suerte de cartas (tres 3, tres fuertes, el macho), no por leaks.

**Verdad suerte/skill (los 3 partidos):** casi todos los puntos se definieron por las CARTAS repartidas (yo gané con macho/hembra/bravas; el bot ganó con sus monstruos). Las decisiones del bot fueron sanas salvo el quiero score-blind, ya corregido.

**Siguen pendientes:** FIX C (ofensiva de envido conservadora — no cantar 23-24 de mano) y el SANDBAG/trampa (leer que el rival que concede la 1ª y canta la 2ª guardó cartas buenas).
