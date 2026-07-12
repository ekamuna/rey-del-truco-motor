"""Modelado del rival (opponent modeling): el bot arma la "fama" de cada usuario.

Referencia: ``docs/PERFIL-DEL-RIVAL.md``. Estadística interpretable (no ML pesado).
"""

from truco.perfil.facetas import Contexto, Faceta
from truco.perfil.perfil import PerfilDelRival

__all__ = ["Contexto", "Faceta", "PerfilDelRival"]
