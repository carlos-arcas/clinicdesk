from __future__ import annotations

from wsgiref.util import setup_testing_defaults

from clinicdesk.web.healthz import get_app


def _llamar(path: str, method: str = "GET") -> tuple[str, list[tuple[str, str]], bytes]:
    environ: dict[str, str] = {"PATH_INFO": path, "REQUEST_METHOD": method}
    setup_testing_defaults(environ)
    estado: str = ""
    headers: list[tuple[str, str]] = []

    def _start_response(status: str, response_headers: list[tuple[str, str]]) -> None:
        nonlocal estado, headers
        estado = status
        headers = response_headers

    body_chunks = get_app(environ, _start_response)
    return estado, headers, b"".join(body_chunks)


def test_healthz_devuelve_ok() -> None:
    estado, headers, body = _llamar("/healthz")
    assert estado == "200 OK"
    assert ("Content-Type", "application/json") in headers
    assert body == b'{"status":"ok"}'


def test_healthz_devuelve_404_fuera_de_ruta() -> None:
    estado, _, body = _llamar("/otra")
    assert estado == "404 Not Found"
    assert body == b'{"status":"not_found"}'
