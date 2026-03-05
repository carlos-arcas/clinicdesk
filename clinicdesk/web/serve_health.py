"""Servidor WSGI mínimo para exponer `/healthz` en contenedor."""

from __future__ import annotations

import os
from wsgiref.simple_server import make_server

from clinicdesk.web.healthz import get_app


def main() -> int:
    puerto = int(os.getenv("APP_PORT", "8000"))
    with make_server("0.0.0.0", puerto, get_app) as servidor:
        servidor.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
