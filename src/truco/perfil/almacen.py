"""Persistencia de perfiles: un archivo JSON por usuario.

Referencia: ``docs/PERFIL-DEL-RIVAL.md`` §2.

Simple y legible. El usuario se sanea para usarlo como nombre de archivo.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from truco.perfil.perfil import PerfilDelRival

#: Carpeta por defecto donde se guardan los perfiles (datos del usuario, local).
DIR_PERFILES = Path("perfiles")


class AlmacenDePerfiles:
    """Carga y guarda perfiles en disco (JSON por usuario)."""

    def __init__(self, directorio: Path = DIR_PERFILES) -> None:
        self._dir = directorio

    def cargar(self, usuario: str) -> PerfilDelRival:
        """Devuelve el perfil del usuario; si no existe, uno nuevo vacío."""
        ruta = self._ruta(usuario)
        if not ruta.exists():
            return PerfilDelRival(usuario=usuario)
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return PerfilDelRival.desde_dict(datos)

    def guardar(self, perfil: PerfilDelRival) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        ruta = self._ruta(perfil.usuario)
        ruta.write_text(json.dumps(perfil.a_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def _ruta(self, usuario: str) -> Path:
        return self._dir / f"{_sanear(usuario)}.json"


def _sanear(usuario: str) -> str:
    limpio = re.sub(r"[^a-z0-9_-]+", "-", usuario.strip().lower())
    return limpio.strip("-") or "invitado"
