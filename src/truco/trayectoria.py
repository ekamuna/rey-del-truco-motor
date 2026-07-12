"""La trayectoria de una ronda: la secuencia de pasos que realmente ocurrieron.

Cada :class:`Paso` guarda el estado antes, quién actuó, qué acción tomó y el
estado después. El bucle de juego la arma; el :mod:`truco.perfil` la lee al
final de la ronda para modelar al rival. Módulo neutral (sin ciclos de import).
"""

from __future__ import annotations

from dataclasses import dataclass

from truco.core.acciones import Accion
from truco.core.state import EstadoRonda


@dataclass(frozen=True, slots=True)
class Paso:
    antes: EstadoRonda
    quien: int
    accion: Accion
    despues: EstadoRonda
