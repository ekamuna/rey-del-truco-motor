# Modelado del rival — el bot conservador que aprende a leer (y a explotar)

> Nuestro camino documentado (el "libro" viene después). El bot **core es
> conservador** (farolear sin nada pierde a la larga), pero **capta insights del
> rival y los aprovecha**, como un humano que piensa en miles de escenarios.
> Todo se aprende SÓLO de lo que se destapa en un showdown (fidelidad).

## Principio
- **No mentimos** (el bot no farolea sin nada). Modelar al rival es para **leerlo y
  explotarlo**, no para imitarlo.
- **Todo por evidencia destapada**: una lectura sólo se registra si hubo showdown
  (envido con "quiero" y tanto mostrado, o truco jugado hasta ver las cartas). Si el
  rival cantó y foldeamos, no aprendemos nada — como en la vida real.
- **Conservador por defecto, explotador cuando hay confianza.** Sin datos jugamos la
  línea segura; con evidencia suficiente ajustamos.

## Facetas del rival (se estiman con Beta-Bernoulli, por rival)
| Faceta | Qué es | Cómo se detecta (showdown) | Cómo se explota |
|---|---|---|---|
| **FAROLERO_ENVIDO** | canta envido con tanto bajo | quiso su envido y mostró tanto < 27 | le pago más / lo cazo (baja el piso) |
| **PESCADOR_ENVIDO** | es mano, tiene puntos, NO canta | fue mano, no cantó, showdown revela 26+ | NO le canto de valor con poco (sólo con 26+) |
| **CONSERVADOR** | no canta salvo mano muy buena | no cantó teniendo 24-25 | le puedo cantar pero puede darme que no |

## Regla 1 — "el mano que no canta el envido"
Cuando el mano juega una carta **sin cantar el envido**, señala tanto bajo… salvo que
sea **pescador** (un buen jugador pesca con 26+ para trampear). Equity del pie al
cantarle de valor (Monte Carlo 400k), según cuánto pesca el rival:

| tanto pie | rival no pesca | pesca 50% | pescador puro |
|---|---|---|---|
| 22 | 0.65 | 0.56 | **0.49** |
| 24 | 0.76 | 0.66 | 0.59 |
| **26** | 0.92 | 0.80 | **0.70** |
| 28 | 1.00 | 0.92 | 0.85 |

**Política:**
- **Default (rival desconocido): cantar de valor desde 26** — seguro incluso contra un
  pescador puro (0.70). Es la línea conservadora.
- **Confirmado NO pescador** (histórico sin pescas): bajar el umbral a ~22-24 y explotar
  su debilidad (0.65-0.76).
- **Confirmado PESCADOR** (lo pescamos una vez con puntos): sólo cantar con 26+.

Es el **espejo del piso de selección**: "si el rival CANTA, tiene → cuidate" (piso);
"si el rival NO canta siendo mano, casi siempre está flojo → cobrale, salvo que pesque".

## Detección del pescador (cómo se junta la evidencia)
En las primeras manos, si el rival es mano y **no canta**, el bot juega el truco (no
canta él tampoco) hasta llegar al showdown, y ahí clasifica por el tanto revelado:
- tanto ≥ 26 y no cantó → **pesca++** (pescador).
- tanto 24-25 y no cantó → conservador.
- tanto < 22 → normal/flojo.
Con eso ajusta la Regla 1 por rival.

## Estado
- [x] FAROLERO_ENVIDO: contador honesto + baja del piso + mixing (`memoria_faroles.py`).
      Medido: vs un farolero de envido, el bot pasa de 43% → 50% aprendiendo a cazarlo.
- [x] PESCADOR_ENVIDO + Regla 1: detección honesta ("mano no cantó y su tanto quedó
      visible ≥26" — showdown de envido o 3 cartas jugadas) + value-cant adaptativo.
      Medido: el bot **distingue** al pescador (tasa 37%) del honesto (7%); vs el honesto
      explota (71.5%→73.5%), vs el pescador se queda seguro (76.5%→77.5%). Rival de test:
      `pescador_real`. Todo OFF por defecto (panel idéntico).
- [ ] Consolidar más señales de `_senales.py` con el modelo.
- [ ] Más facetas/escenarios a medida que aparezcan jugando (truco: farol/pesca; etc).
