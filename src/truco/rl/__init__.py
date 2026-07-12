"""Aprendizaje por refuerzo (RL): la máquina aprende su estrategia sola.

Referencia: ``docs/ROADMAP.md`` M6.

v1: Q-learning tabular por self-play. El "modelo" es una tabla legible
``(estado abstracto, acción) → valor``. No hay red neuronal (eso es el techo).
Aprende **las apuestas** (cantar/querer/no querer/farolear); la elección de qué
carta jugar es una heurística fija.
"""
