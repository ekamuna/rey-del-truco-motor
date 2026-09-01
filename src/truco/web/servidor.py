"""Servidor web mínimo (biblioteca estándar, sin dependencias) para jugar al truco.

Comando: ``uv run truco-web`` → abrí http://127.0.0.1:8000 en el navegador.
Para jugar desde el celu en la misma red: ``uv run truco-web --host 0.0.0.0`` y entrá
a ``http://<ip-de-tu-compu>:8000``.

Una sola partida en curso a la vez (uso personal). El marcador de partidas
ganadas/perdidas se guarda en ``datos/marcador-web.json`` y sobrevive reinicios.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from truco.web.juego import Juego, Marcador

_HTML = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
_RUTA_MARCADOR = Path("datos/marcador-web.json")


class _Estado:
    """Estado del proceso: el marcador persistente y la partida en curso."""

    def __init__(self) -> None:
        self.marcador = Marcador.cargar(_RUTA_MARCADOR)
        self.juego = Juego(self.marcador)

    def nueva(self) -> None:
        self.juego = Juego(self.marcador)

    def guardar(self) -> None:
        self.marcador.guardar(_RUTA_MARCADOR)


class _Handler(BaseHTTPRequestHandler):
    estado: _Estado  # inyectado en main()

    def log_message(self, *args: object) -> None:  # silencio el log de acceso
        pass

    def _json(self, data: dict[str, object]) -> None:
        cuerpo = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _html(self) -> None:
        cuerpo = _HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._html()
        elif self.path == "/api/estado":
            self._json(self.estado.juego.vista())
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path == "/api/nueva":
            self.estado.nueva()
        elif self.path == "/api/jugar":
            largo = int(self.headers.get("Content-Length", 0))
            try:
                cuerpo = json.loads(self.rfile.read(largo) or b"{}")
                indice = int(cuerpo["indice"])
            except (ValueError, KeyError, TypeError):
                self.send_error(400, "indice inválido")
                return
            self.estado.juego.jugar(indice)
        else:
            self.send_error(404)
            return
        self.estado.guardar()
        self._json(self.estado.juego.vista())


def main() -> None:
    parser = argparse.ArgumentParser(description="Rey del Truco — jugá en el navegador.")
    parser.add_argument("--host", default="127.0.0.1", help="0.0.0.0 para jugar desde el celu")
    parser.add_argument("--puerto", type=int, default=8000)
    args = parser.parse_args()

    _Handler.estado = _Estado()
    servidor = HTTPServer((args.host, args.puerto), _Handler)
    donde = "127.0.0.1" if args.host in ("127.0.0.1", "localhost") else args.host
    print("🃏 Rey del Truco — servidor web listo")
    print(f"   Abrí:  http://{donde}:{args.puerto}")
    if args.host == "0.0.0.0":
        print("   (desde el celu en la misma red: usá la IP de esta compu)")
    print("   Ctrl-C para cortar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n¡Chau! 🃏")
        servidor.server_close()
