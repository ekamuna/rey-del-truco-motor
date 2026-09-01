# ENVIDO + CANAL DE INFORMACIÓN — Informe de estudio

Motor Rey del Truco (1v1). Todo sale del solver exacto: para cada mano propia se enumeran las C(37,3)=7770 manos posibles del rival y se cuenta showdown de envido. El `tanto` está validado contra `truco.core.scoring.tanto_envido` con **0 mismatches sobre las 9880 manos** C(40,3). No hay muestreo ni RNG: es enumeración cerrada.

Convención de asientos: **mano gana los empates de envido, pie los pierde.** Esto es lo que da vuelta toda la intuición de cartas (donde el pie rinde más). En envido, a igual tanto, **la mano siempre vale más que el pie.**

---

## 1) Tabla de envido — P(ganar) en showdown

`p_mano` y `p_pie` = probabilidad de ganar el envido a cara descubierta contra un rival de mano aleatoria (sin condicionar a que el rival haya cantado). No existen tantos entre 8 y 19: sin par de palo el máximo es 7, y los pares arrancan en 20.

| Tanto | P(mano) | P(pie) | Brecha (mano−pie) |
|------:|--------:|-------:|------------------:|
| 0  | 0.0057 | 0.0000 | +0.0057 |
| 1  | 0.0174 | 0.0085 | +0.0089 |
| 2  | 0.0391 | 0.0228 | +0.0163 |
| 3  | 0.0740 | 0.0479 | +0.0261 |
| 4  | 0.1251 | 0.0869 | +0.0382 |
| 5  | 0.1955 | 0.1429 | +0.0526 |
| 6  | 0.2883 | 0.2189 | +0.0694 |
| 7  | 0.4066 | 0.3182 | +0.0884 |
| 20 | 0.4339 | 0.4041 | +0.0298 |
| 21 | 0.4681 | 0.4375 | +0.0306 |
| 22 | 0.5061 | 0.4755 | +0.0306 |
| 23 | 0.5590 | 0.5116 | +0.0474 |
| 24 | 0.6119 | 0.5645 | +0.0474 |
| 25 | 0.6801 | 0.6162 | +0.0639 |
| 26 | 0.7484 | 0.6845 | +0.0639 |
| 27 | 0.8325 | 0.7519 | +0.0806 |
| 28 | 0.8744 | 0.8322 | +0.0422 |
| 29 | 0.9179 | 0.8743 | +0.0436 |
| 30 | 0.9459 | 0.9178 | +0.0281 |
| 31 | 0.9748 | 0.9459 | +0.0289 |
| 32 | 0.9872 | 0.9748 | +0.0124 |
| 33 | 1.0000 | 0.9872 | +0.0128 |

**Lecturas clave:**
- **Punto de favorito (p ≥ 0.50):** de mano en el **22** (0.506); de pie recién en el **23** (0.512). Estar de pie te cuesta ~1 tanto de umbral, porque perdés los empates.
- **Extremos coherentes:** 33 de mano = **1.000** (invencible, gana hasta el empate 33-33). 33 de pie = **0.9872** (NO es lock: perdés el empate contra otro 33). Tanto 0 de pie = 0.0000 (nunca ganás), de mano 0.0057 (solo empatás contra otro 0).
- **Monotonía:** ambas columnas son no-decrecientes en el tanto. La brecha mano−pie es **estrictamente positiva en las 22 categorías** — nunca el pie iguala o supera a la mano.

---

## 2) Capa de APUESTAS

Dos decisiones distintas, con umbrales distintos. Ojo con no confundirlas.

### Break-even
- **QUERER un envido simple: BE = 0.25.** Arriesgás 1 tanto extra para ganar 3 (el pozo). Si tu P(ganar) condicionada ≥ 0.25, querés.
- **CANTAR de valor: BE = 0.50** en showdown (ser favorito). Por debajo, cualquier canto es farol / fold-equity, no valor.

### CANTAR — desde qué tanto es valor
| | Cantar-valor (p_show ≥ 0.50) | Zona situacional (solo fold-equity) |
|---|---|---|
| **Mano** | desde **22** (p=0.506) | 20-21 (0.434 / 0.468) |
| **Pie** | desde **23** (p=0.512) | 20-22 (0.404 / 0.437 / 0.476) |

Debajo del umbral cantás únicamente por fold-equity (que el rival no quiera), nunca porque seas favorito.

### QUERER — umbral por asiento y disciplina del rival
El querer va **condicionado a que el rival YA cantó** (mostró fuerza ≥ su umbral). Por eso el umbral de querer es MÁS ALTO que el de cantar: no te enfrentás a una mano aleatoria, sino a una que ya se declaró fuerte.

Mínimo tanto con P ≥ 0.25 *dado* el canto del rival:

| Tu asiento | vs rival agresivo (canta 24) | vs rival normal | vs rival tight (canta 29) |
|---|---|---|---|
| **Mano** | desde 25 | desde 27 (rival normal canta 26/27) | desde 29 |
| **Pie** | desde 26 | desde 28 | desde 30 |

**Canónico (rival-mano canta 26 / rival-pie canta 27):** break-even de querer en **27 de mano** y **28 de pie**.

### INVERSIÓN CLAVE (el corazón de la estrategia)
El umbral de **cantar** (22/23) es más bajo que el de **querer** (27/28). Consecuencia directa:

> **Tu par medio (22-26 de mano, 23-27 de pie) se canta EN OFENSA pero se foldea EN DEFENSA.**

Números de referencia que lo prueban:
- **27 de mano** gana **83.3%** en showdown, pero solo **32.5%** si un pie te cantó primero → aun así querés (0.325 > 0.25).
- **27 de pie** gana **75.2%** en showdown, pero solo **21.0%** frente a un canto de mano → **NO querés** (0.210 < 0.25).

### ZONAS TRAMPA
1. **Trampa real (cantás de valor pero NO querés el re-canto).** La equity condicionada a que el rival cantó se derrumba.
   - De **mano**: tantos **22-26** cantan de valor (showdown 0.506-0.748) pero q_27 = 0.00 → foldeás al re-envido de un caller disciplinado.
   - De **pie**: tantos **23-27** cantan de valor (0.512-0.752) pero q_26 va de 0.00 a 0.210 (< BE 0.25) → no querés el canto de un mano que mostró ≥26.
   - **Regla:** par medio = canta-de-valor en ofensa, fold en defensa, *salvo* contra rivales agresivos (contra un caller que canta 24, la mano 25-26 empieza a querer: q_24 ≈ 0.26-0.27).

2. **Slowplay (querés obvio pero NO cantás primero, para inducir).** 31-33 son monstruos. De mano conviene checkear / esperar el canto rival y escalar a real/falta en vez de espantarlo cantando de entrada.

### Regla de la FALTA SEGURA
La falta como jugada de valor blindado (p ≥ ~0.975):
- **De mano:** desde **31** (0.975), casi blindada en 32 (0.987), **LOCK absoluto en 33** (1.000 — gana el empate 33-33).
- **De pie:** recién desde **32** (0.975). **Ojo: 33 de pie NO es lock** (0.987), porque perdés el empate contra otro 33.
- **Nunca** la falta con tanto ≤ 30 fuera de un ajuste por marcador (fix por estado del juego, no por equity de la mano).

---

## 3) EL CANAL DE INFORMACIÓN — el envido como dato para el juego de cartas

Idea: el envido cantado (o no cantado) es un **canal de información** sobre las cartas del rival. Medimos cuánto mueve la equity del **juego de truco** conocer ese dato, comparando `equity_sin_info` (belief plano) contra `equity_con_info` (belief filtrado por la acción de envido).

### Deltas medidos (enumeración exacta, bit-idénticos en dos corridas)

| # | Escenario | Sin info | Con info | Δ |
|---|---|---:|---:|---:|
| 1 | Sos PIE; el mano cantó envido ≥27 (25.0% de manos); tu mano BBF (3-oro, 2-copa, 4-basto) | 0.7445 | 0.6629 | **−0.0816** |
| 2 | Sos PIE; el mano NO cantó (regla del mano que no canta, <27, 75.0%); misma BBF | 0.7445 | 0.7717 | **+0.0272** |
| 3 | Sos PIE; el mano cantó GRANDE ≥31 (real/falta, 6.6%); misma BBF | 0.7445 | 0.6712 | **−0.0733** |
| 4 | Sos MANO; el pie cantó tight ≥29 (11.6%); tu mano monster (macho, 7-espada, 6) | 1.0000 | 1.0000 | **0.0000** |
| 5 | Sos MANO; el pie cantó agresivo ≥24 (45.8%); tu mano floja (12, 11, 10 = tres figuras) | 0.5296 | 0.6183 | **+0.0887** |
| 6 | Sos PIE; el mano NO cantó (<26, 65.4%); tu mano floja (12, 11, 10) | 0.5678 | 0.5285 | **−0.0393** |

**El signo del delta NO es fijo.** Depende de tu propia mano. El driver físico: las cartas de más envido (**7-espada y 7-oro, ambas valor 7**) son también cartas TOP del truco. Entonces:
- Condicionar a envido alto **sube** P(rival tenga un 7 bravo): de 14.6% base a **28% (≥27)** y **53% (≥33)** → le mete una carta top de truco a la mano.
- Pero **baja** la fuerza total media (15.5 → 11.9 a ≥31), porque para armar un par grande el rival compromete dos cartas al mismo palo, a menudo bajas.
- Los dos efectos compiten. Si tu mano ya gana salvo contra los 7 bravos, el pruning por "cantó" te **baja** equity (Sc1, Sc3). Si tu mano ya pierde contra casi todo, el par bajo del rival te **sube** equity (Sc5).

### REGLA DE PODA para el PIMC (Perfect Information Monte Carlo)
Al muestrear las 3 cartas del rival para simular el juego de cartas: **calculá el tanto de cada muestra y rechazá las inconsistentes con la acción de envido observada.** El tanto se computa con el mismo `tanto_envido` validado (0 mismatches).

Intervalos de aceptación por acción y asiento del rival:

1. **Rival CANTÓ de valor** → keep solo `tanto_rival ≥ T_cant`. Umbrales: rival-mano normal **26**, rival-pie normal **27**, agresivo **24**, tight **29**. Si **escaló** (envido-envido / real / falta con ganas) subí T_cant a **29-31**.
2. **Rival es MANO y NO cantó** (tuvo el derecho primero y pasó = *regla del mano que no canta*) → keep solo `tanto_rival < 26`. Sesga su mano a tanto flojo.
3. **Rival foldeó / no quiso NUESTRO envido** → keep solo `tanto_rival < BE de querer` (mano 26, pie 27). No tenía para aceptar.
4. **Nadie cantó / info nula** → no podar (belief plano).

**SOFT-PRUNE obligatorio (nunca cliff duro sobre pool chico):**
- (a) Si tras filtrar quedan <200 muestras, ensanchá la banda ±2 tantos alrededor del umbral.
- (b) Mejor: en vez de aceptar/rechazar binario, **pesá cada muestra por P(rival canta | su tanto)** con una sigmoide centrada en T_cant (ancho ~2-3 tantos) y hacé best-response ponderado. Esto captura el farol / semi-farol: el rival no siempre canta con tanto ≥ T.

**El mayor salto "juega la carta → juega al truco":** el escenario donde el canal más pesa es **Sc5 (Δ = +0.089)** — mano floja de tres figuras frente a un pie que cantó agresivo ≥24: la equity de cartas salta de 0.530 a 0.618, casi 9 puntos, y eso puede dar vuelta un querer/no-querer de retruco. El extremo opuesto es **Sc1 (Δ = −0.082)**. La banda operativa del canal es **|Δ| ≈ 0.03–0.09**.

**Regla de oro para el bot:** recomputá el best-response sobre el belief podado; **no** apliques un ajuste de signo fijo.

---

## 4) CONFIANZA — auditoría

**Veredicto: SÓLIDO.** Ninguna discrepancia > 1pp. Se re-corrieron los solvers canónicos (`PYTHONPATH=src`, `.venv`).

- **(a) Tabla de envido — 12/12 celdas** (no solo 6-8) coinciden con `canonical_envido.py --benchmark` hasta el redondeo. Ejemplos: 20 mano 0.4339=0.433927 / pie 0.4041=0.404062; 25 mano 0.6801=0.680130 / pie 0.6162=0.616157; 27 mano 0.8325=0.832547 / pie 0.7519=0.751924; 29 mano 0.9179=0.917891 / pie 0.8743=0.874342; 31 mano 0.9748=0.974808 / pie 0.9459=0.945882; 33 mano 1=1.0 / pie 0.9872=0.987198. Máx desvío ~0.0004pp (redondeo del 4º decimal).
- **Validación del tanto:** 0 mismatches sobre las 9880 manos vs `truco.core.scoring.tanto_envido`.
- **(b) Refutado que P(pie) ≥ P(mano) en envido:** sobre las 22 categorías de tanto realizables, **P(mano) ≥ P(pie) SIEMPRE**, con brecha estrictamente positiva en TODAS (mano gana empates, pie los pierde, y siempre hay prob de empate > 0). **0 violaciones.** Es la INVERSA de la intuición de cartas ("el pie siempre rinde más" — cierto para fuerza de carta en CARTA-TRUCO.md, pero NO para envido).
- **(c) Coherencia de extremos OK:** 33 → P(mano)=1.0; 0 → P(mano)=0.0057, P(pie)=0.0; ambos asientos monótonos no-decrecientes en el tanto.
- **(d) Canal reproducible:** `canal_info.py` da deltas bit-idénticos en dos corridas (−0.0816, +0.0272, −0.0733, +0.0000, +0.0887, −0.0393); enumeración exacta determinista sin RNG; su tanto también valida 0 mismatches.

**Reconciliación de solvers:** las 3 implementaciones coinciden EXACTAMENTE celda por celda a 6 decimales (16 celdas: 8 tantos × 2 asientos). No hay bug que corregir. Única diferencia: `impl_0` usa una sola pasada (rápido); `impl_1`/`impl_2` llaman `solve_envido` por asiento (~2× más lento, por eso hicieron timeout de 2 min al re-correr). El canónico usa la pasada única de `impl_0`.

### Salvedades honestas
- El benchmark de la tabla es **showdown incondicional**. La capa de QUERER (condicionada al umbral de canto del rival) **no está tabulada** ahí; se obtiene truncando la distribución rival a `rt ≥ umbral`. El solver lo soporta filtrando el rival en `solve_envido`.
- El ejemplo CLI `"7 6 4"` **no trae palos**: se asigna la convención de palos distintos (e/b/o/c) → tanto 7. Formato completo: `"7e 6e 4o"`.
- El **valor del canal es MODESTO** (efecto de segundo orden): vale ~0.00 cuando tu mano ya está decidida (Sc4: monster, sin=con=1.0). No da vuelta una mano claramente fuerte ni salva una claramente perdida. Los umbrales de disciplina del rival (agresivo/normal/tight) son **supuestos de modelo**, no medidos contra un pool de rivales reales: hay que calibrarlos con datos de juego.

---

## 5) Conexión con el mapa del cerebro y qué codeamos primero

**Dónde encaja en el cerebro del bot:**
- La **tabla de envido** es una lookup table pura (tanto × asiento → p_win). Es el equivalente al `hand_strength` de cartas: capa 0, sin dependencia de belief. Va cableada como constante precomputada.
- La **capa de apuestas** (cantar/querer, umbrales, falta segura) es la **policy de envido**: un módulo de decisión que toma (tanto, asiento, acción del rival, disciplina estimada, marcador) → {cantar, querer, no querer, escalar}. Es determinista dado el modelo del rival.
- El **canal de información** es el **puente entre el sub-juego de envido y el sub-juego de cartas**: alimenta el belief del PIMC. Es el primer lugar donde los dos módulos dejan de ser independientes y se hablan.

**Qué codeamos primero (orden propuesto):**
1. **Lookup de envido + validador de tanto.** Ya está el solver canónico; portarlo a la lib como tabla congelada + test que re-valida 0 mismatches sobre las 9880 manos. Barato, es el cimiento y la fuente de verdad.
2. **Policy de envido con los umbrales del punto 2.** Cablear cantar-valor (mano 22 / pie 23), querer condicionado (mano 27 / pie 28 canónico), zonas trampa y falta segura. Parametrizar la "disciplina del rival" (agresivo/normal/tight) como input, con default = normal.
3. **Pruning por consistencia de tanto en el PIMC** (punto 3), directamente con **soft-prune sigmoide** — no el cliff duro. Como el tanto ya se calcula, el canal es **gratis**: se suma como filtro/peso sobre el belief antes del best-response de cartas.
4. Recién después, **calibrar la disciplina del rival** contra datos de partidas (los umbrales 24/26/27/29 son supuestos, no medidos).

**Regla de diseño transversal:** el canal corrige decisiones borderline de truco (querer/no-querer cerca del 50%) y conviene cablearlo, pero **nunca dejar que domine**. Efecto de segundo orden frente a tu propia mano: es ajuste fino, no game-changer.

---

## FIX G — implementación del canal en el bot (commit `940b4a3`)

El canal de información quedó implementado en el PIMC:
- **Motor:** `EstadoObservable.envido_rival` (señal derivada en `observacion_de`): `"rival_canto"`
  (cantó y no hubo showdown → tanto ALTO), `"rival_no_quiso"` / MANO `"nadie_canto"` (→ tanto BAJO,
  la regla del que no canta), `"sin_info"`.
- **PIMC:** `_restriccion_tanto_por_envido` traduce la señal en una banda `[piso, techo]` de tanto;
  `_candidatas`/`_muestrear_rival`/`_cumple_tanto` la aplican al imaginar las cartas del rival.
  Banda BLANDA (umbral ± `_MARGEN_ENVIDO=2`, no corte duro) + fallback (si la poda deja el belief
  vacío → sin poda). El umbral es el MISMO ajustado por la caza-faroles (Canal 3 del mapa): contra
  un canta-todo la vara baja sola → robusto.
- **Panel NEUTRO** (75.3% → 75.3%): los rivales mecánicos no correlacionan envido con cartas.

### Límite real observado jugando (seed 77, ronda 11)
FIX G poda por **tanto**, pero el **hembra/macho/anchos** son cartas TOP del truco con tanto BAJO
(el ancho cuenta 1). Entonces "el mano no cantó → tanto flojo" **NO implica cartas flojas** cuando el
rival tiene un ancho. El canal roza en contra en esas manos (el signo del Δ depende de la mano, ya
medido en el estudio). La banda blanda + fallback lo amortiguan; para afinarlo haría falta condicionar
también por la ESTRUCTURA de cartas, no sólo el tanto.

### FIX H — modelado de truco (el leak, RESUELTO)
El bot **quería demasiado los cantos de truco del humano** con manos flojas (seed77 r1/r8/r10/r11).
Causa: `_prob_gana_cartas` imaginaba las manos del rival UNIFORMES, ignorando que el rival ELIGIÓ
cantar. FIX H cierra el Canal 3 (modelo del rival) para el truco, en dos etapas:

- **Etapa 1 (piso de estructura, commit `9625626`):** al RESPONDER un truco, cada mano imaginada del
  rival se pondera por P(el rival cantaría con ella): 1.0 si tiene estructura (`_rival_tiene_estructura_truco`,
  espejo de `_estructura_para_cantar_truco`), ε si no. Las manos flojas pesan ε → baja mi P(gano) →
  foldeo los pagos flojos. Panel neutro (75.3→75.4).
- **Etapa 2 (ε adaptativo, commit `a67901a`):** `MemoriaFaroles.truco_faroles` cuenta (Beta-Bernoulli)
  los cantos de truco SIN estructura, aprendiendo SÓLO de rondas donde se vieron las 3 cartas del rival
  (fidelidad, como el envido). `_epsilon_farol_truco` lleva ε del default a la tasa observada: rival
  TIGHT → ε baja (foldeo más), FAROLERO → ε sube (le pago y le cazo el bluff). Panel realista caza-ON
  74.4→**75.1** (+0.7), faroleros sanos.

**Demostración del fix (mismo spot, el bot aprendió que soy tight):** respondiendo mi truco de apertura
con "1 fuerte + media + basura", P(gano) uniforme (bot viejo) = **0.28 → QUERÍA** (el leak); ponderado
(FIX H) = **0.09 → NO QUIERE**. El flip exacto que sangraba.
