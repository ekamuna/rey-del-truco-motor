# PerfilDelRival — Diseño (borrador para pensar juntos)

> El bot deja de jugar "contra un humano genérico" y empieza a jugar **contra VOS**:
> te observa, arma tu **fama** y ajusta cuándo te cree y cuándo no.
> Esto es **opponent modeling** (modelado del rival). NO es machine learning pesado:
> es estadística interpretable que funciona desde la primera partida.

**Estado:** ✅ **Implementado** (v1) en `src/truco/perfil/` — este documento es el diseño detrás. El bot de reglas lo usa cuando pasás `--usuario <nombre>`; se guarda en `perfiles/<usuario>.json`.

---

## 1. La idea

Hoy el bot decide con umbrales fijos (`si tanto >= 27, canto`). Con el PerfilDelRival, esos
umbrales se **corren según quién tenés enfrente**: si sos mentiroso, te acepta con menos; si te
asustás fácil, te farolea más. Y — clave — lo hace mirando **tu historial real acumulado**.

---

## 2. Identidad y persistencia por usuario

- Cada jugador tiene un **usuario** (ej. `juan-perez`). Al arrancar, te "logueás" con ese nombre.
- El bot carga **tu perfil histórico** (de todas tus partidas anteriores) y lo sigue actualizando.
- **Almacenamiento (v1):** un archivo JSON por usuario en `perfiles/<usuario>.json`. Simple, legible,
  versionable, sin base de datos. (Más adelante se podría migrar a SQLite si crece.)
- Se **carga al loguear**, se **actualiza al final de cada ronda** (cuando se ven las cartas) y se
  **guarda al terminar la partida** (o incrementalmente).
- "Login" en v1 = pasar el nombre: `uv run truco --usuario juan-perez` (o preguntarlo al inicio).
  Sin contraseña: es un juego local, el usuario es solo una **etiqueta** para separar historiales.

> **Privacidad:** son tus propios datos, guardados **localmente** en tu máquina. Si algún día el juego
> fuera online, esto pasa a ser dato sensible y hay que tratarlo con cuidado. Por ahora, local y tuyo.

---

## 3. Qué observa el bot (la materia prima)

La clave: **al final de cada ronda se revelan las cartas**, así que el bot puede comparar lo que
CANTASTE con lo que REALMENTE tenías. Cada ronda produce "observaciones" etiquetadas con el **contexto**
en que pasaron:

| Evento observado | Qué se registra |
|---|---|
| Cantaste truco/retruco | ¿tu mano era fuerte o débil? (verdad revelada) |
| Cantaste envido | ¿tu tanto era alto o bajo? |
| Te fuiste al mazo | ¿en qué situación? |
| Dijiste quiero / no quiero | ¿con qué mano? |
| **Contexto de cada evento** | marcador (ganando/parejo/perdiendo), bazas de la ronda, racha reciente, si sos mano |

Cada observación es un par **(¿hiciste X?, en el contexto C)** → con eso se arman los porcentajes.

---

## 4. Las facetas del perfil

El perfil no es un número: son varias **facetas**, cada una una probabilidad estimada. Estas son
TODAS las facetas que queremos (el "norte"); las marcadas **[v1]** se implementan primero.

1. **[v1] Mentiroso / farolero de truco** (tu idea principal)
   `P(tu mano era débil | cantaste truco)`. Cuando apostás al truco, ¿qué tan seguido es humo?
   → alto ⇒ el bot te acepta el truco con manos más flojas.

2. **[v1] Mentiroso de envido**
   `P(tu tanto era bajo, < 27 | cantaste envido)`. El mismo concepto, en el envido.

3. **[v1] Miedoso / cauteloso**
   `P(dijiste "no quiero" | te cantaron truco)`. Si te asustás fácil → el bot te farolea más.

4. **[norte] Agresivo / picante**
   `P(escalás | ya hay un canto)` — cuánto subís a retruco / real envido / falta.

5. **[norte] Manotazo / pescador**
   `P(te vas al mazo | mano fea)` — cuán rápido abandonás vs cuánto peleás.

6. **[norte] Revanchista** — no es una faceta nueva sino un **contexto** (ver §5): el mentiroso
   medido específicamente cuando venís de perder. Se captura condicionando las facetas por momento.

> **Alcance v1:** facetas 1-3, condicionadas por contexto `{ganando / parejo / perdiendo}`.
> Las facetas 4-5 y contextos más finos (racha exacta) quedan como el norte, ya documentados acá.

---

## 5. Tendencias según el momento

Una faceta **no es un solo número**: depende del **contexto**. Tu ejemplo es perfecto:
*"si perdió 2-3 manos seguidas, hay predisposición a mentir para recuperar"*.

Entonces cada faceta se mide **por contexto**, no en general. Ejemplos de contexto:

- **Según el marcador:** `mentiroso[ganando]` vs `mentiroso[parejo]` vs `mentiroso[perdiendo]`.
- **Según la racha:** `mentiroso[venís de perder 2+ manos]` (el "revanchismo" que dijiste).
- **Según seas mano o pie.**

Así el bot puede pensar: *"en general este jugador miente 30%... pero **perdiendo y en racha negativa**
miente 55% → ahora mismo no le creo casi nada"*. Eso es lo que lo hace sentir vivo.

---

## 6. Cómo se representa técnicamente (el "mini-ML" interpretable)

Cada faceta-en-un-contexto es un **contador de dos números**: `(veces_que_pasó, oportunidades)`.
El porcentaje es `veces_que_pasó / oportunidades`. Dos detalles importantes:

- **Prior (para arrancar sin datos):** con una sola observación, `1/1 = 100% mentiroso` sería absurdo.
  Se arranca con una creencia neutral (ej. "supongo 30% hasta que me demuestres otra cosa") y los datos
  la van corriendo. Fórmula: `(veces + α) / (oportunidades + α + β)`. Esto es un **modelo Beta-Bernoulli**
  — el mismo tipo de razonamiento bayesiano que usa el ML, pero acá **transparente y auditable**.
- **Confianza:** con pocas observaciones, la estimación es tentativa. El bot puede mostrar
  *"todavía te estoy conociendo"* hasta juntar N datos, y recién ahí confiar fuerte.

> Esto es un puente hermoso al ML: es **aprendizaje de la experiencia**, online, pero donde podés
> **abrir la libreta y ver por qué** el bot decidió lo que decidió. Interpretable de punta a punta.

---

## 7. Cómo influye en las decisiones del bot

Los umbrales de `ConfigReglas` dejan de ser fijos y se **corren según el perfil + el contexto actual**:

```
umbral_efectivo_para_aceptar_truco = umbral_base − k · mentiroso[contexto_actual]
```

- Rival **mentiroso** → bajo el umbral: le acepto el truco con manos más flojas (sus apuestas son humo).
- Rival **miedoso** → subo mi frecuencia de farol: le canto truco con manos más débiles (va a foldear).
- Rival **perdiendo y en racha** → si su `mentiroso[perdiendo]` es alto, ahora mismo desconfío más.

La decisión sigue siendo `if/else` legible; el perfil solo **mueve los números**.

---

## 8. Dónde encaja en la arquitectura

- **Motor intacto.** El perfil vive en la capa de agentes/aplicación, no en `core`.
- **Nuevo hook en el Agente:** hoy `observar_resultado(recompensa)` solo pasa +1/−1. Para modelar al
  rival hace falta ver el **estado final revelado** (ambas manos + qué se cantó). Propuesta: agregar
  `observar_ronda(estado_final)` a la interfaz `Agent` (default no-op), que el `game_loop` llama al
  terminar cada ronda. El `AgenteReglas`-con-perfil lo usa para actualizar la libreta.
- **`PerfilDelRival`** (objeto por usuario) + **`AlmacenDePerfiles`** (carga/guarda JSON por usuario).
- El `AgenteReglas` se construye con el perfil del oponente y lo consulta al decidir.
- **Testeable:** las facetas son funciones puras sobre contadores → fáciles de testear
  (ej. "tras 10 rondas donde mintió 6, `mentiroso ≈ 0.5`").

---

## 9. Decisiones abiertas (para resolver juntos)

1. **¿Qué facetas para la v1?** Propongo arrancar con **mentiroso (truco)**, **miedoso** y **mentiroso
   de envido**. ¿Sumás/sacás alguna?
2. **¿Qué cuenta como "mano débil"** para detectar un farol? (definir un umbral de fuerza, ej. sin
   cartas de fuerza ≥ 8).
3. **Contextos de la v1:** ¿arrancamos solo con `{ganando / parejo / perdiendo}` + `racha negativa`, o
   más simple todavía (solo racha)?
4. **Login:** ¿flag `--usuario` o pregunta al inicio? ¿un usuario "invitado" por defecto?
5. **¿Cuántas observaciones** antes de que el bot "confíe" en una faceta y lo empiece a explotar?
6. **¿Le mostramos al jugador su propia fama?** (ej. un comando "ver mi perfil"). Divertido, pero le
   avisa al rival que lo estás leyendo.

---

## 9-bis. Terminología (importante) y parámetros configurables

**Ojo con la palabra "aprende".** Está sobrevalorada acá: el sistema no "entiende"
nada. **Acumula una estadística (cuenta) y decide comparando un número contra un
umbral.** Es más honesto decir "guarda y estima" que "aprende". (En la jerga del
ML igual se le dice "aprender parámetros de datos", pero conviene tener claro qué
es lo que realmente pasa: contar y dividir.)

**Todas las aristas son configurables** (para poder revisarlas sin tocar la lógica):

- `ConfigPerfil` (cómo se *mide* la fama):
  - `fuerza_mano_debil` (qué es "mano fea" para detectar un farol de truco) — **definición
    provisoria a revisar**: hoy es "la mejor carta no llega a un 2".
  - `tanto_envido_bajo` (qué tanto es "bajo" para un farol de envido).
  - `prior_alfa` / `prior_beta` (la opinión previa / las "partidas imaginarias").
  - `umbral_contexto` (diferencia de puntos para ganando/perdiendo).
- `ConfigReglas` (cómo se *usa* la fama):
  - `k_aceptar_truco`, `k_aceptar_envido`, `k_farolear_truco` (cuánto pesa cada faceta).
  - `ancla_perfil` (punto neutro: con la estimación en este valor, no se ajusta nada).
  - Poniendo los `k` en 0, el bot ignora el perfil por completo.

## 10. Por qué este es el paso ideal antes del ML

- Es **interpretable**: entendés cada decisión (a diferencia de una red neuronal).
- Te enseña conceptos reales de ML **sin el andamiaje pesado**: estimación online, prior bayesiano,
  contexto/condicionamiento, cold-start.
- Hace el juego **notablemente más divertido** ya.
- Deja la infraestructura (persistencia por usuario, hook de observación) lista para cuando llegue el
  ML de verdad.
