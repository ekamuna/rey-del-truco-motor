# Lógica del truco del experto (conservadora, fundada en equity)

> El truco se gana con **2 bazas**. La apuesta sigue tu **certeza** de esas 2 bazas.
> Todo fundado en conteo exacto (el truco es finito: 40 cartas, el rival toca 3),
> no en corazonada. Teoría del experto, fundada en equity enumerada exhaustivamente.

## Los números que fundan la regla (enumeración exhaustiva)

**Vale4 / escalar — P(el rival tenga una carta que le gane a mi carta ganadora):**

| Mi carta ganadora | La superan | Al arranque (rival: 3 de 37) | En la 3ª baza (rival: 1) |
|---|---|---|---|
| macho | 0 | 0% → vale4 | 0% → vale4 |
| hembra | 1 | **8.1%** → vale4 | 2.9% → vale4 |
| 7 espada | 2 | 15.8% → límite | 5.7% → vale4 |
| 7 oro | 3 | 23% → NO | 8.6% → vale4 |
| un 3 | 4 | **29.8% → NO** | 11.4% → límite |
| un 2 | 8 | 53% → NO | 22.9% → NO |

La regla "≤1 carta te gana → vas" es exacta: al arranque **sólo macho/hembra** dan >90%.
El vale4-con-un-3 (que 4 cartas superan) era ~30% → jamás. Y la misma carta cambia según
cuántas quedan sin ver → **escalar es de end-game y hay que CONTAR** (por eso el `prob≥0.80`
fijo del PIMC fallaba: no contaba y el slow-play lo engañaba).

**La trampa (voy 1-0 con desempate, me cantan la 2ª) — P(gano), enumerando las 561 manos:**

| Mis 2 cartas | P(gano) vs rival aleatorio | riesgo (manos que me ganan) |
|---|---|---|
| brava + basura | 91% | 9% |
| 3 + basura | 80% | 20% |
| dos medias | 97% | 3% |
| media + basura | 50% | 50% |
| basura pura | 31% | 69% |

El desempate hace 1-0 fortísimo por default → **casi siempre QUIERO**; foldeo sólo con
media+basura o peor. PERO un sandbagger fino te canta *justo* con las manos del "riesgo"
(por eso te regaló la 1ª) → contra ese, P(gano) real ≈ (100 − riesgo). → foldeo más si el
rival tiene el patrón "me concedió la 1ª y me canta" registrado.

## Árbol de decisión

1. **Yo canto (ofensiva)** — sólo con estructura de 2 bazas: 2-0; o gané ≥ las que perdí
   con una carta FUERTE (fuerza≥8); o baza 1 con ≥2 cartas fuertes. **Nunca 1 carta + basura.**
   Con monstruo, slow-play para hacerlos entrar.
2. **Me cantan (respuesta)** — leo la situación: de arranque decido por mi mano; en la
   TRAMPA (me dieron la 1ª y cantan) quiero por default salvo media+basura, más fold si es
   sandbagger conocido; yendo ellos 1-0 foldeo salvo 2 cartas fuertes.
3. **Escalar (retruco/vale4)** — sólo con **>90%**: cuento las cartas sin ver que me ganan;
   si P(rival tenga ≥1) < 10% (≤1 al arranque, casi cualquier brava en la 3ª) y voy
   adelante/parejo en bazas → escalo. Si no, quiero flat.
4. **Baza decisiva** — reacciono a su carta: gana → quiero/canto; emparda + hice primera →
   quiero; pierde → mazo.
5. **Marcador** — mucho→hacer entrar, poco→irse/ver, medio→ir viendo; cerca de 15 no arriesgo.

## Implementado (FIX A, 2026-07-13)

En `agents/pimc.py`:
- `_p_rival_supera(obs, carta)` — P(el rival supere mi carta) por hipergeométrica exacta
  sobre las cartas sin ver + cuántas le quedan al rival.
- `_estructura_para_cantar_truco(obs)` — la regla de 2 bazas (2-0 / 1-0+fuerte / baza1 con
  2 fuertes). Gatea el canto ofensivo y la escalada.
- `_escalar_o_querer_truco` — ahora escala sólo con `_p_rival_supera(mejor) < 0.10` +
  estructura + prob≥0.80 (antes: `prob≥0.80` solo, que el slow-play inflaba → farol de vale4).
- Medido (60 partidas, panel mecánico+realista): **winrate-neutral** (seed 11: 78.0%=78.0%;
  seed 22: 71.5% vs 70.2%). La dif/partido baja un poco (escala menos) = corta los farols
  sin perder partidos. El panel subvalora el fix (los rivales mecánicos no castigan el farol
  como un humano). TDD: `test_escala_truco_solo_con_carta_casi_imbatible`,
  `test_estructura_para_cantar_exige_dos_bazas`, `test_p_rival_supera_cuenta_las_que_ganan`.

## Pendiente (próximos fixes de esta tanda)
- **La TRAMPA / sandbag** (respuesta): condicionar las manos imaginadas en "me concedió la
  1ª y canta" → subir la vara para querer. (El PIMC hoy no lee eso.)
- **Envido defensa por frecuencia** (Target #1): pagar 26+ si el rival canta envido seguido.
- **Envido ofensiva conservadora**: cantar de mano sólo con tanto fuerte (no 23-24).

## Implementado (FIX D, 2026-07-13)
`_lidero_baza_decisiva(obs)`: tras una parda con bazas parejas (g==p), la baza que lidero
DEFINE la mano → `_liderar` juega la carta MÁS ALTA (antes: siempre la más baja en baza 2+,
que en el desempate post-parda regalaba manos ganadas — error R12 de la partida seed 7).
Medido winrate-neutral (A+B+D 75.2% vs A+B 75.0%, 120 part × seeds 11/22/33); corrige el
bug sin costo (el panel lo subvalora: el spot es raro, contra humano importa). TDD:
`test_lidera_mas_alta_en_baza_decisiva_tras_parda`. 155 tests.

## Implementado (FIX E, 2026-07-13) — escalada de envido consciente del marcador
`_escalar_o_querer`: si voy GANANDO y cerca del final (falta ≤ 5, o sea líder ≥ 10),
canto FALTA ENVIDO en vez de real — la falta gana el partido y CAPA el riesgo. Antes
escalaba por tanto solamente (30 → real envido), ciego al marcador: iba 13 con envido 30
y cantaba REAL (arriesga 5) → si perdía, el rival en 10 llegaba a 15 y ganaba. Yendo ATRÁS
sigue escalando normal (una real ganada da vuelta el partido; la falta ahí le daría el
partido al rival). Catch del usuario en la partida seed 21 (R13). Winrate-neutral (A+B+D+E
75.3% vs A+B+D 75.2%). TDD: `test_escalar_envido_usa_falta_cerca_del_final`. 156 tests.
Nota relacionada: cuando el envido ya te lleva a 15, el partido está definido (no hace
falta jugar el truco); el motor cierra bien al fin de la ronda.
