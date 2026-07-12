"""Tests de persistencia de perfiles (JSON por usuario)."""

from pathlib import Path

from truco.perfil.almacen import AlmacenDePerfiles, _sanear
from truco.perfil.perfil import PerfilDelRival


def test_cargar_usuario_nuevo_da_perfil_vacio(tmp_path: Path) -> None:
    alm = AlmacenDePerfiles(tmp_path)
    p = alm.cargar("nuevo")
    assert p.usuario == "nuevo"
    assert p.conteos == {}


def test_guardar_y_cargar_round_trip(tmp_path: Path) -> None:
    alm = AlmacenDePerfiles(tmp_path)
    p = PerfilDelRival("Emmanuel Abugauch")
    p.conteos["mentiroso_truco|parejo"] = (3, 5)
    p.conteos["miedoso|perdiendo"] = (1, 8)
    alm.guardar(p)

    recargado = alm.cargar("Emmanuel Abugauch")
    assert recargado.conteos == p.conteos
    assert (tmp_path / "emmanuel-abugauch.json").exists()


def test_sanear_nombre_de_usuario() -> None:
    assert _sanear("Emmanuel Abugauch") == "emmanuel-abugauch"
    assert _sanear("  ") == "invitado"
    assert _sanear("José/../hack") == "jos-hack"
