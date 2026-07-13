# Lectura del rival — heurísticas del experto (para el PIMC)

> Conocimiento de un jugador experto (miles de partidas) para **inferir las cartas
> ocultas** del rival. Cada regla restringe o sesga las manos que el PIMC imagina,
> acercándolo al oráculo (que ve las cartas y gana ~90%).

## 1. La restricción del envido (la más fuerte)
El tanto cantado + las cartas mostradas suelen **determinar** la mano.
- Ej: cantó **28**, jugó **2 de copa**, después **7 de oro** → la tercera es **sí o sí
  1 de oro** (par de oro 7+1=8→28) **o 6 de copa** (par de copa 2+6=8→28).
- Regla para el motor: **solo imaginar manos cuyo tanto coincida con el cantado.**

## 2. Ocultar los puntos
Con un buen envido, a veces tira primero una carta que NO es del palo de los puntos,
para no revelar por dónde vienen. Si cantó 28 y jugó una carta suelta, los puntos
están en las **dos que le quedan**.

## 3. Envido no querido → tenía puntos
Si cantó envido y no quisiste, asumí que **tenía tanto** → sus cartas tienden a su
**palo fuerte**. Si después juega un 5 de espada, probablemente **tenga más espada**.
Eso ayuda a decidir el truco.

## 4. Truco cantado "de una" (sin mostrar carta)
Ambiguo: puede estar **mintiendo** o tener mucho. Hay que ver cómo se desarrolla la
mano. Señal de baja confianza (no descartar el farol).

## 5. Carta alta primero + truco después
Si gana la primera con una carta alta y **después** canta truco, puede estar
**tapando** que las otras dos son malas (representar fuerza que no tiene).

## 6. Teoría del mano a mano (a probar con combinatoria)
En 1v1, si el rival ya mostró dos cartas mid/altas (ej. 3-espada y 1-copa), es muy
probable que su tercera sea **una negra baja** (4/5/6 o 7 malo). → puede justificar
aceptar un truco en tercera aun con mano floja (7 de basto).

## 7. Slow-play / trampa (jugada de ataque, no de lectura)
Con mano fuerte, **dejar que el rival gane la primera** para que se confíe y cante
truco, y ahí **revirárselo** (retruco) → sacás 3 en vez de asustarlo matando la primera.

---
*Estado: heurísticas 1-6 son de INFERENCIA (sesgan el muestreo del PIMC). La 7 es de
POLÍTICA (cómo jugar). La #1 es la de mayor impacto y la más fácil de implementar.*
