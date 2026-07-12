# REGLAMENTO INTERNO — Rey del Truco (Motor)

Especificación **precisa y orientada a implementación** de las reglas que va a respetar el motor.
Base construida sobre reglamentos canónicos (juegosdesalon + reglamento de torneo de Rentas) + correcciones del experto del proyecto.

> **Estado:** `v0.2` — **base lista para implementar la v1**. Se afina durante las pruebas.
> El **faroleo** (§10) es estrategia, no reglamento → se trabaja más adelante (no bloquea el motor).
> Cada punto marcado 🚩 es una decisión de diseño tomada (no un default silencioso).

## §0. Alcance de la v1
- **Modalidad:** 1 vs 1 (mano a mano). No hay compañeros → **no hay señas**.
- 🚩 **Sin flor** en la v1 (queda especificada en §9 detrás de un flag `con_flor`, se implementa en un milestone aparte).
- 🚩 **Partida configurable:** `PARTIDA_A ∈ {15, 30}`. Malas/buenas solo aplican a 30.
- 🚩 **Falta envido:** variante simple (§4).

---

## §1. Cartas y jerarquía

Baraja española de **40 cartas**, 4 palos (espada, basto, oro, copa), valores 1-7, 10, 11, 12. **Sin 8 ni 9.**

### Jerarquía de truco (fuerza para ganar bazas) — de mayor a menor
| Rango | Carta(s) | Nota |
|------:|----------|------|
| 1 | 1 de espada | brava (macho) |
| 2 | 1 de basto | brava (hembra) |
| 3 | 7 de espada | brava |
| 4 | 7 de oro | brava |
| 5 | los 3 | |
| 6 | los 2 | |
| 7 | 1 de copa / 1 de oro | "ases falsos" |
| 8 | 12 (rey) | |
| 9 | 11 (caballo) | |
| 10 | 10 (sota) | |
| 11 | 7 de copa / 7 de basto | "sietes falsos" |
| 12 | los 6 | |
| 13 | los 5 | |
| 14 | los 4 | |

- Solo las **4 bravas** son cartas únicas. Del rango 5 al 14, las cuatro cartas del mismo número **empatan entre sí** (misma fuerza) → si se enfrentan, **parda**.
- Trampas de implementación: el **1 falso** (copa/oro) es bajo (rango 7), el **7 falso** (copa/basto) es débil (rango 11).

### Valor de envido (distinto de la fuerza de truco)
- Figuras (10, 11, 12) → **0**. Resto → su número (1..7).
- Dos cartas del **mismo palo**: `20 + valor_carta_a + valor_carta_b`.
- Tres palos distintos: vale la **carta más alta** sola (su valor de envido).
- Rango posible: **0 a 33** (33 = 6 y 7 del mismo palo + 20).

---

## §2. Reparto e inicio
- En 1v1, uno es **mano** (juega primero, gana los empates) y el otro es **pie** (reparte esa ronda).
- El rol de **mano alterna** cada ronda.
- Se reparten **3 cartas** a cada uno, de a una.
- 🚩 Azar **reproducible**: el barajado usa una semilla (`seed`) para poder repetir partidas al depurar y entrenar.

---

## §3. Estructura de una ronda (mano)
- Se juegan hasta **3 bazas**. Cada baza la gana la carta de mayor jerarquía (§1). Mismo rango = **parda**.
- Baza 1: arranca el **mano**. Bazas 2 y 3: arranca **quien ganó la baza anterior**. Si una baza fue parda, arranca el **mano**.
- No hace falta jugar bazas de más si la ronda ya está definida.

### Resolución de la ronda — tabla completa (incluye pardas) ⭐
Esta es la parte que rompe los motores mal hechos. Regla general: **gana quien "pega" primero; el mano solo gana si NO hubo ningún ganador de baza.**

| Caso | Resultado |
|------|-----------|
| Un jugador gana **2 bazas** | gana ese jugador |
| Gana la 1ª y **emparda** la 2ª | gana ese jugador (no hace falta 3ª) |
| **Emparda** la 1ª y gana la 2ª | gana ese jugador |
| **1-1** (cada uno ganó una) → decide la 3ª | gana quien gane la 3ª |
| **1-1** y la 3ª es **parda** | 🚩 gana **quien ganó la PRIMERA baza** (¡no el mano!) |
| Parda la 1ª, alguien gana la 2ª | gana el de la 2ª |
| Parda la 1ª y la 2ª → decide la 3ª | gana quien gane la 3ª |
| **Las 3 pardas** | gana **el mano** |

> Corrección respecto de v0.1: en un **1-1 con la 3ª parda NO gana el mano**, gana **el que ganó la primera baza**. El mano solo se lleva la ronda cuando **las tres bazas son pardas**.

---

## §4. El envido
**Cuándo:** solo en la **primera baza**, y solo **antes de jugar la primera carta** propia (o antes de querer el truco). Una vez jugada la primera carta o querido el truco, ya no se puede cantar envido.

### Cantos y valores (si hay QUIERO)
| Canto | Vale (querido) |
|-------|----------------|
| Envido | 2 |
| Envido + Envido | 4 (2+2) |
| Real Envido | 3 |
| Falta Envido | 🚩 `PARTIDA_A − puntos_del_puntero` (mín. 1) |

- Se pueden **encadenar** subiendo, sin orden fijo (se puede cantar Real Envido directo, o Falta Envido directo).
- Ejemplo de cadena: `Envido (2) → Real Envido (+3) → Falta`. El valor "querido" es la suma de lo aceptado.

### Respuesta NO QUIERO
- Se paga lo **acumulado querido antes** del último canto rechazado; si el rechazado era el **primer** canto, se paga **1**.
- Ejemplos: `Envido → no quiero` = **1**. `Real Envido → no quiero` = **1**. `Envido → Real Envido → no quiero` = **2** (el envido simple ya "valía"). `Real Envido → Falta → no quiero` = **3**.

### Resolución (si hay QUIERO) — cantar el tanto y mostrar
- Gana el **tanto más alto**. **Empate → gana el mano.**
- 🚩 **Falta envido (simple):** vale lo que le falta al **puntero** (el que va ganando) para llegar a `PARTIDA_A`. Si van iguales, se toma ese puntaje. (Elegido sobre la variante de torneo "a buenas/a ganar".)

**Ritual del tanto (importante, define la UI):**
1. Se **cantan los tantos** en orden (empieza el **mano**); el que tiene menos puede decir **"son buenas"** en vez de su número, para **no revelar** sus cartas de cara al truco.
2. Las cartas del envido se **muestran recién al final de la mano** (después del truco), no en el momento.
3. **Regla anti-mentira:** el ganador del envido **debe mostrar** las cartas para cobrar. Si no las muestra (o se va sin mostrar), **pierde los puntos del envido Y los del truco** (se los lleva el rival).

**Digitalización (1v1 vs máquina):** el motor conoce las cartas y es la **fuente de la verdad** → nadie puede mentir el tanto, la regla se cumple sola. Se traduce a flujo de UI:
- El motor **auto-resuelve** quién ganó el envido, pero **no revela** las cartas hasta el fin de la mano (preserva la info para el truco).
- **Botón "Mostrar"** al terminar la mano → revela y **acredita** los puntos.
- La penalización por **mal-declarar** el tanto solo aplica en un futuro **modo humano-vs-humano** (flag), donde un humano sí podría cantar un tanto falso.

---

## §5. El truco
**Cuándo:** en cualquier momento de la ronda (lo usual, a partir de la baza 2).

| Canto | Vale (querido) | NO QUIERO paga |
|-------|----------------|----------------|
| Truco | 2 | 1 |
| Retruco | 3 | 2 |
| Vale Cuatro | 4 | 3 |

- Solo se puede **subir** después de haber dicho **quiero** explícito al nivel anterior.
- Vale Cuatro es el tope: aceptado, se juegan las cartas y el ganador de la ronda cobra 4.
- Si nadie canta truco, la ronda vale **1**.

---

## §6. Orden de cantos y "el envido está primero"
- Orden general: **(flor) → envido → truco**.
- Si en la primera baza un jugador canta **truco** antes de que el rival haya cantado envido, el rival puede responder cantando **envido primero**: se resuelve el envido y **después** se retoma el truco pendiente.
- Regla de palabra: los cantos **obligan**. Decir "quiero"/"no quiero" o "flor" fuera de lugar cuenta como jugada. (Relevante para la UI/parser, no tanto para el motor 1v1.)

---

## §7. Irse al mazo
- Abandonar la ronda tirando las cartas boca abajo.
- El rival cobra lo que estaba en juego en ese momento (si no se había cantado truco, cobra **1**; si había truco querido, cobra el valor del truco; el envido ya resuelto se cobra aparte).
- 🚩 *Pendiente confirmar con experto:* el punto exacto que cobra el rival según qué cantos había en curso (ver §10).

---

## §8. Fin de la ronda y puntaje
- Se suman al marcador: lo del **envido** (si hubo) + lo del **truco**/ronda.
- **Partida a 30 (larga):** primeras 15 = **malas**, segundas 15 = **buenas**.
- **Partida a 15 (corta):** sin distinción de malas/buenas.
- Gana quien llega primero a `PARTIDA_A`.

---

## §9. Flor (OPCIONAL — flag `con_flor`, NO en v1)
> Especificado para el futuro. No se implementa en la v1.
- Hay flor con **3 cartas del mismo palo**. Es **obligatorio cantarla**. Si hay flor, **no hay envido**.
- Valor de la flor: `20 + suma de las 3 cartas` (solo para comparar cuál gana).
- Cantos: **Flor** = 3 · **Contraflor** = 6 · **Contraflor al resto** = a ganar (+3 por flor).
- Respuestas: "con flor quiero", "con flor me achico", "contraflor", "contraflor al resto".
- 🚩 *Al implementarla, definir con el experto la variante exacta de contraflor y el "pido flor".*

---

## §10. Faroleo, trampas y lógicas de experto  ⬅️ SECCIÓN ABIERTA
> Acá va el conocimiento del experto: cómo se miente en envido y en truco, las trampas
> de reglamento que valen la pena modelar, y las lógicas de decisión. Pendiente de carga.

### 10.1 Faroleo en el truco
_(pendiente)_

### 10.2 Faroleo en el envido
_(pendiente)_

### 10.3 Trampas / jugadas de reglamento a modelar
_(pendiente)_

### 10.4 Lógicas de decisión del experto (para el bot y el PerfilDelRival)
_(pendiente)_

---

## §11. Qué cubre la implementación v1 (M4/M5) y simplificaciones

**Implementado y testeado** (motor `truco.core`): jerarquía y pardas, reparto por semilla,
envido / real envido / falta envido (cadena, quiero/no quiero, empate al mano, falta simple),
truco / retruco / vale cuatro (quiero/no quiero), "el envido está primero", irse al mazo,
y partida acumulativa a 15/30 con alternancia de mano.

**Simplificaciones conscientes de la v1** (a revisar/ampliar más adelante):
- El **envido-envido** (responder "envido" a un "envido") está permitido hasta 2 veces; el resto
  de la cadena es envido → real → falta.
- El "envido primero" se modela con **una** suspensión de truco (suficiente para 1v1); no hay
  anidamientos más profundos.
- El **bot de reglas** todavía no aprovecha el "envido primero" ni farolea (eso es §10, más adelante).
- Sin **flor** (flag futuro, §9).
