# La carta de póker del truco (1v1, solo cartas)

Estudio del valor de cada mano de 3 cartas en el truco cara a cara, **sin envido**, contra un rival codicioso. Cada mano se clasifica por su estructura en 20 arquetipos combinando cuatro alturas:

- **B (basura)** = negras y chicas, fuerzas 0–3 (cuatros, cincos, seis, 7-falsos)
- **M (media)** = fuerzas 4–7 (dieces, onces, doces)
- **F (fuerte)** = el dos (f8) y el tres (f9)
- **V (brava)** = las cuatro matadoras: 7-oro (f10), 7-espada (f11), hembra/ancho-basto (f12), macho/ancho-espada (f13)

`P(mano)` y `P(pie)` son la probabilidad de ganar la mano de truco jugando primero (mano) o segundo (pie), promediadas sobre todas las manos del arquetipo. **Pie siempre rinde más que mano**: ver la carta que lidera el rival antes de comprometerte es información pura.

---

## 1) La tabla madre (ordenada por P de mano, de peor a mejor)

| # | Arq. | P(mano) | P(pie) | Línea óptima (resumen) | Dónde ganás |
|---|------|:------:|:-----:|------------------------|-------------|
| 1 | **BBB** | 0.042 | 0.088 | Puro duck. De mano liderás siempre la más baja y emparejás; el orden casi no importa, todas pierden. De pie empardás si tenés carta igual (para dejar viva la baza y robar), si no duckeás. | Solo si al rival le toca una mano igual o más débil (trío en basura y sin nada que supere tus cartas clave). Hueco mínimo: (2,3,3)=0.205 es el techo; (0,0,0)=0. |
| 2 | **BBM** | 0.111 | 0.270 | La media es tu única arma y con dos basuras necesitás robar 2 bazas → la escondés. De mano liderás basura baja y guardás la media para 2ª/3ª. De pie brilla: superás barato cuando el rival lidera algo < tu media. | Rival sin fuertes ni bravas y con al menos una carta que tu media supera. La altura de la media manda: (3,3,7)=0.343 vs (0,1,4)=0.027. Pie duplica a mano. |
| 3 | **BBF** | 0.214 | 0.461 | La fuerte es robo casi seguro (le gana a todo salvo bravas). No la quemás: de mano liderás basura baja y reservás el 2/3 para clavar una baza. De pie superás casi cualquier lidera con la fuerte. | Rival sin brava y encima robás una 2ª baza. tres(f9) rinde más que dos(f8): (2,3,9)=0.447 vs (2,3,8)=0.354. Dos basuras al piso hunden todo: (0,0,9)=0.004. |
| 4 | **BMM** | 0.292 | 0.420 | No liderar nunca la media. De mano duckeás baza1 con la basura y peleás 2 y 3 con las medias (la menor que gane). De pie superás barato o empardás para conservar tempo. | Tu tope es una media (≤f7): la supera cualquier fuerte o brava (~18 cartas por encima). Solo ganás si el rival no tiene más de UNA sobre-carta. |
| 5 | **BBV** | 0.335 | 0.543 | La brava fija 1 baza pero con dos basuras necesitás una 2ª. **No quemás la brava de arranque**: (1,2,13) liderar basura f1=0.478 vs liderar el macho=0.088. La reservás para la baza decisiva. | La brava fija una baza; ganás la mano si robás la segunda (rival con 2 cartas bajo tus basuras). macho>7-oro apenas: (2,3,13)=0.665 vs (2,3,10)=0.563. |
| 6 | **BMF** | 0.420 | 0.682 | De mano duckeás baza1 con la basura y guardás media+fuerte para 2 y 3. El fuerte roba una casi seguro; necesitás que la media gane la segunda. De pie (salto enorme, 0.68) superás lo mínimo y guardás el fuerte. | Rival sin carta que supere tu fuerte Y tu media alcanza para una 2ª baza. Hueco doble: esquivar bravas sobre el fuerte y colocar la media. |
| 7 | **MMM** | 0.551 | 0.595 | De mano liderás una media INTERMEDIA (f5) buscando parda o robar barato; no malgastar la más alta. De pie duckeás con la más baja lo que no podés superar, empardás/superás barato lo igual o menor. | Grupo más flojo, ninguna carta domina. Ganás con dos cartas rivales por debajo de tus medias o enganchando pardas. (4,4,4)=0.32 → (6,7,7)=0.76. |
| 8 | **BMV** | 0.613 | 0.854 | **Aun con brava, duckeás baza1 con la basura** (liderar la brava desploma el P). Guardás la brava para ganar la 2ª y la media pelea la otra. De pie (0.85) tomás barato la baza que quieras. | Tu brava es casi invencible (solo la superan bravas mayores). Ganás casi siempre que la brava tome una baza Y consigas una 2ª con la media o parda. |
| 9 | **BFF** | 0.657 | 0.773 | **Excepción: se lidera FUERTE** (y mano≈pie). De mano abrís con un fuerte para llevártela o forzar gasto de brava, y guardás el otro fuerte. No duckear. | Dos fuertes que solo superan las 4 bravas = dos ganadores. P(rival sin bravas)=0.702 → ganás. Perdés casi solo si le entran ≥2 bravas (2.6%). |
| 10 | **MMF** | 0.677 | 0.780 | De mano liderás la MEDIA más alta y ESCONDÉS el fuerte; rematás con el fuerte. De pie superás barato con las medias y sacás el fuerte solo contra sus cartas altas. | Un fuerte que pelea 1 baza + dos medias de apoyo. Ganás si conseguís una 2ª con media o parda. Perdés si entra brava con soporte. |
| 11 | **MMV** | 0.837 | 0.902 | De mano liderás con la MEDIA MÁS BAJA, NUNCA la brava. La brava se guarda para robar una baza segura; las medias cazan respuestas bajas. | Tu carta seria es la brava. Ganás la mano si conseguís la 2ª baza con media o parda. Perdés solo si entra carta > tu brava Y te tapan una media. |
| 12 | **BFV** | 0.840 | 0.926 | De mano **liderás la basura** para esconder tus dos altas; después ganás 2 y 3 con fuerte y brava. Reservás la brava intacta; no la quemás contra una carta chica. | Brava (≈1 baza) + fuerte que pelea la segunda. Perdés solo si entran DOS cartas por encima del fuerte. (2,9,13)≈0.96; (0,8,10)=0.70. |
| 13 | **MFF** | 0.855 | 0.902 | De mano liderás el FUERTE MÁS BAJO (f8), no el f9 ni la media; cazás barato y guardás el f9 de martillo. De pie superás barato con la media y respondés con el fuerte mínimo. | Dos altas casi-clavadas (dos y tres): a cada una solo la superan las 4 top. Perdés solo si entran ≥2 de las top-4 (~2.6%). |
| 14 | **FFF** | 0.924 | 0.945 | De mano liderás de frente con el tres (f9); casi indistinto del dos. Barrés todo ≤9 y duckeás solo cuando responden brava. De pie superás barato con el dos y reservás el tres. | Tu tope f9 solo lo superan las 4 bravas. Ganás salvo que al rival le entren ≥2 bravas. |
| 15 | **MFV** | 0.930 | 0.971 | De mano liderás el FUERTE (f8) y guardás la BRAVA como segunda ganadora; forzás al rival a gastar una alta. De pie: media abajo, fuerte al medio, brava reservada para lo alto. | Dos altas en gamas separadas (fuerte + brava): el rival tiene que superar AMBAS. Con macho ~0.99. |
| 16 | **BVV** | 0.957 | 0.967 | De mano liderás la brava más alta y seguís con la otra; ganan baza 1 y 2 salvo que te superen ambas. De pie superás con la brava mínima que gane. | Dos de las 4 top del mazo. Con macho o 12+13 → P=1. Único hueco: par 10+11 y que al rival le entren 12 y 13 juntas (~0.9%). |
| 17 | **FFV** | 0.981 | 0.986 | De mano **liderás el FUERTE, no la brava** ((13,9,8) fuerte=0.997 vs macho=0.950): escondés la brava de seguro. De pie superás barato con el fuerte y sacás la brava solo cuando el fuerte no gana. | La brava propia cubre una de las 4 top; perdés solo con bravas ESTRICTAMENTE mayores en cantidad para 2 bazas. Con macho ~0.9999. |
| 18 | **MVV** | 0.984 | 0.991 | Dos de las 4 invencibles, mano prácticamente hecha. De mano liderás cualquier brava y rematás con la otra. De pie las dos bravas cubren casi todo. | Perdés solo si el rival tiene las DOS bravas restantes y ambas mayores: solo posible con par 10+11 (~0.9%). |
| 19 | **FVV** | 0.997 | 0.998 | Con dos bravas casi da igual el orden. El orden solo importa en triples sin macho (11+10+8): ahí liderás el fuerte y guardás las dos bravas. Con macho ganás siempre. | Dos bravas tapan dos de las 4 top. Perder requiere las otras 2 bravas juntas por encima → imposible con macho. |
| 20 | **VVV** | 1.000 | 1.000 | Juego resuelto. Liderás la más baja de las tres y guardás las dos de arriba; da igual. No hay decisión. | 3 de las 4 cartas más altas. No existe reparto del rival que te gane la mano. |

---

## 2) Reglas emergentes (fundadas en los números)

**Regla 1 — Escondé la buena, no la lideres.** Cuando tenés UNA sola carta ganadora (una brava o un fuerte) rodeada de basura/media, liderarla de arranque es el error más caro del juego. Ganás esa baza pero perdés las otras dos y caés OPP 2-1:
- BBV (1,2,13): liderar basura f1 = **0.478** vs tirar el macho de entrada = **0.088**. Tirar el macho primero te cuesta ~39 puntos de winrate.
- BBF (2,3,9): liderar basura f2 = **0.447** vs liderar el tres = **0.204**.
- BMV, MMV, BFV: mismo patrón. La brava/fuerte es un martillo para la baza que decide, no para la que se regala.

**Regla 2 — El punto de quiebre es "cuántas cartas ganadoras tenés".**
- **Una sola ganadora** (BB*, BM*, MM*) → jugás a esconder y a robar la 2ª baza. Tu P depende de que el rival NO tenga soporte, no de tu propia carta. Muy explotable la altura: media alta > media baja, tres > dos, macho > 7-oro.
- **Dos ganadoras** (BFF, BFV, MFF, MFV, FF*, *VV) → cambiás de plan: liderás fuerte, forzás gasto, y perdés SOLO si al rival le entran ≥2 sobre-cartas. Ahí el winrate salta al 0.84–0.99. Esta es la firma del "valor puro".
- **Tres ganadoras** (FVV, VVV) → juego resuelto, no hay decisión.

**Regla 3 — BFF es la excepción que confirma: con dos fuertes se LIDERA.** Es el único arquetipo del bloque bajo donde mano ≈ pie (0.657 vs 0.773): tener dos cartas fuertes premia la iniciativa. Detalle fino de la auditoría: con (1,8,9) lo óptimo es liderar el **dos (f8)=0.622**, no el tres (f9)=0.581. Liderás fuerte, pero el MENOR de los dos fuertes.

**Regla 4 — Dos basuras al piso arruinan cualquier carta top.** Tener el tres o una brava no salva la mano si las otras dos son las más bajas del mazo: (0,0,9)=0.004, (0,0,10)=0.004. La 2ª baza es la que ganás o perdés; sin nada que pelee la segunda, la carta monstruo solo te da un 1-1 que perdés en la tercera.

**Regla 5 — La altura importa donde hay UNA carta; deja de importar donde hay DOS.** En BBM la media f7 vale el doble que la f4. En BBV el macho apenas supera al 7-oro (0.665 vs 0.563) porque igual ganás la baza; lo que cambia es el conteo de pardas y quién lidera después. En MVV/FVV/VVV la altura es irrelevante salvo el borde 10+11.

**Regla 6 — Pie vale entre +5 y +25 puntos de winrate.** El salto mano→pie es máximo en el bloque medio (BMF 0.42→0.68, BMV 0.61→0.85, BBM 0.11→0.27): ahí ver la carta líder te deja superar o duckear con precisión. En los extremos (VVV, BBB) la información casi no cambia nada porque no hay decisión que tomar.

---

## 3) Capa de apuestas (querer / cantar)

Umbral de referencia para **querer**: ~0.25 de equity (mano). Para **cantar** hay que separar valor (querés que te quieran) de farol (querés que foldeen).

| Arq. | P(mano) | ¿Querer? | ¿Cantar? | Lógica |
|------|:------:|:--------:|:--------:|--------|
| BBB | 0.042 | **NO** | Situacional (farol puro) | Muy por debajo del umbral; cantar solo rinde por fold-equity, nunca +valor si te quieren. |
| BBM | 0.111 | **NO** | NO | Débil para valor y sin farol creíble; de pie (0.27) recién asoma a marginal. |
| BBF | 0.214 | Marginal | Situacional (semi-farol) | Justo bajo 0.25; de pie 0.46 → querer claro. La fuerte da respaldo. |
| BBV | 0.335 | **SÍ** | Situacional (semi-farol) | Querer de mano. Cantar es semi-farol con respaldo de brava, no valor puro. |
| BMM | 0.292 | **SÍ** | NO | Querer, pero **no cantar**: fuerza media con showdown-value; si te quieren estás <50% y te paga solo lo mejor. |
| BMF | 0.420 | **SÍ** | Situacional | Querer. Cantar es valor-fino/semi-farol: +EV solo si el rival abandona peores. |
| MMM | 0.551 | **SÍ** | NO | Querer, pero **no cantar**: clásico showdown-value sin dominio; cantar quema valor. |
| BMV | 0.613 | **SÍ** | **CANTAR-VALOR** | Brava + media = estructura alta, ganás aun cuando te quieren. |
| BFF | 0.657 | **SÍ** | **CANTAR-VALOR** | Dos ganadores; ganás 2 bazas salvo ≥2 bravas rivales. |
| MMF | 0.677 | **SÍ** | **CANTAR-VALOR** | Fuerte + dos medias de apoyo, margen claro. |
| MMV | 0.837 | **SÍ** | **CANTAR-VALOR** | Brava + dos medias; caés solo con carta > brava y te tapan una media. |
| BFV | 0.840 | **SÍ** | **CANTAR-VALOR** | Brava + fuerte en gamas distintas = valor puro. |
| MFF | 0.855 | **SÍ** | **CANTAR-VALOR** | Dos fuertes; perdés solo con ≥2 top-4 (~2.6%). |
| FFF | 0.924 | **SÍ** | **CANTAR-VALOR** | Tres fuertes; necesitan ≥2 bravas para ganarte. |
| MFV | 0.930 | **SÍ** | **CANTAR-VALOR** | Fuerte + brava: tienen que superar ambas. |
| BVV | 0.957 | **SÍ** | **CANTAR-VALOR** | Dos de las 4 top; con macho o 12+13 sos imbatible. |
| FFV | 0.981 | **SÍ** | **CANTAR-VALOR** | La brava cubre una top, dos fuertes el resto. |
| MVV | 0.984 | **SÍ** | **CANTAR-VALOR** | Dos invencibles, casi mano hecha. |
| FVV | 0.997 | **SÍ** (escalar) | **CANTAR-VALOR** | Casi imbatible; escalar a vale-cuatro. |
| VVV | 1.000 | **SÍ** (todo) | **CANTAR-VALOR** | Juego resuelto; escalar al máximo. |

**Los tres casos-trampa de la capa de apuestas** son BMM, MMM y (de mano) BBM: manos que **querés pero no cantás**. Tienen equity de showdown por encima del umbral de querer, pero cuando VOS cantás y te quieren, foldeás solo lo ya perdido y te paga todo lo que te gana → el canto es valor negativo. La frontera del cantar-valor se abre recién en ~0.61 (BMV), no en el umbral de querer.

---

## 4) Confianza de la auditoría y salvedades honestas

**Núcleo cuantitativo: SÓLIDO.** Tres implementaciones independientes del solver coinciden **exactamente** (diff máximo 0.000000) en las 20 celdas del benchmark, pasan las 20 aserciones de resolución de pardas y cruzan 0 mismatches contra el motor real de truco (27 combinaciones de pardas) y el multiset de fuerzas de la baraja. Todas las probabilidades `P` reportadas son exactas al redondeo. La tesis central "esconder la buena / no liderar el monstruo" está confirmada por los números de liderazgo.

**Tres errores de PROSA (no de la tabla de P) detectados por la auditoría adversarial — a corregir en la narrativa:**
1. **BMV**: el texto dice que liderar la brava "se desploma a ~0.08". Falso para (2,5,11): liderar 7-espada da **0.279**, no 0.08 (la dirección —es peor que duckear a 0.633— sí es correcta; el 0.08 quedó arrastrado del caso BBV).
2. **BVV**: dice que con bravas 10+11 "bajás a ~0.84". El best-response real de (2,10,11) mano es **0.905** (minimax 0.856); el 0.84 subestima ~6 puntos.
3. **BFF**: recomienda "liderar el tres". Subóptimo: en (1,8,9) liderar el **dos** (0.622) supera a liderar el tres (0.581). La regla (liderar fuerte) es correcta; la carta específica no.

**Salvedades metodológicas (importantes para no sobrevender el modelo):**
- **Rival codicioso, no óptimo.** Todos los `P` son *best-response* contra un rival fijo que gana barato (mínima carta que supera estricto), descarta bajo y lidera bajo, y que **nunca emparda para salvar baza**. Contra un humano fuerte que sí farolea, emparda y varía, los números de pie —los más explotativos— bajarán. `p_greedy` es un techo explotativo, no un equilibrio.
- **`p_minimax` NO es cota inferior.** El docstring del solver afirmaba que el minimax (info perfecta a ambos) acota por abajo al best-response. Es **falso**: en asiento mano la ganancia de información de uno mismo puede superar la del rival, y se hallaron 12 violaciones (gap máx ~0.02). Son dos juegos distintos; usar `p_minimax` solo como referencia de "mano con info perfecta", no como piso garantizado.
- **Bug latente (no afecta hoy).** El resolver de tres-pardas no recibe el parámetro `mano`, así que atribuye el desempate a ME por defecto; debería ir al líder de baza1 (OPP cuando sos pie). Hoy no cambia ningún número publicado porque esas hojas nunca caen en la línea argmax, pero hay que arreglarlo antes de modelar un rival que busque pardas.
- **Solo cartas: falta el envido.** Este estudio ignora por completo el tanto. Una mano puede ser basura al truco (BBB) y monstruo al envido, y eso cambia radicalmente qué cantás y querés. Es la pieza más grande que falta.

---

## 5) Próximos pasos para meter esto en el bot

1. **Tabla de arquetipos como capa base de decisión.** Clasificar la mano del bot en uno de los 20 arquetipos (map de cada carta a B/M/F/V) y cargar la línea óptima + P(mano)/P(pie) como política de arranque. Es una lookup table de 20 entradas, barata y auditada.
2. **Política de juego de carta** codificada como las reglas emergentes: (a) con 1 ganadora, duckear y esconder; (b) con 2 ganadoras, liderar el fuerte MENOR; (c) VVV/FVV, orden indiferente. Usar el solver canónico (`canonical_solver.py`, CLI JSON) para resolver el desempate carta-a-carta en los casos límite en runtime.
3. **Capa de apuestas** con los tres umbrales: querer≈0.25, no-cantar en la zona de showdown-value (BBM/BMM/MMM), cantar-valor desde ~0.61. Distinguir explícitamente valor de farol para el módulo de agresión.
4. **Corregir los 3 puntos de prosa** (BMV 0.279, BVV 0.905, BFF liderar el dos) si esta narrativa alimenta explicaciones al usuario.
5. **Arreglar el bug del `mano` en el resolver de pardas** antes de subir el nivel del rival modelado.
6. **Modelo de rival más realista.** Reemplazar el rival codicioso por uno con farol/parda/varianza (idealmente CFR o best-response iterado) y recalcular; esperar que pie baje respecto de los números actuales.
7. **Fase siguiente: integrar el envido.** Sin el tanto la política de canto está incompleta; es el mayor upside pendiente para que el bot juegue truco de verdad y no solo "la carta".

---

*Notación: fuerzas 0–13 sobre la baraja de truco. B=0–3, M=4–7, F=8–9, V=10–13. P = probabilidad de ganar la mano (best-response vs rival codicioso, info imperfecta). Solver canónico y benchmark reconciliados en las 20 celdas; diff entre implementaciones = 0.000000.*
