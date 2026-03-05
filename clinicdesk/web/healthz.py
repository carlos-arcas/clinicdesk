"""Endpoint WSGI de salud para despliegues en contenedor."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

LOGGER = logging.getLogger("clinicdesk.healthz")


def _respuesta_json(status: str, payload: dict[str, str]) -> tuple[str, list[tuple[str, str]], list[bytes]]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = [("Content-Type", "application/json"), ("Content-Length", str(len(body)))]
    return status, headers, [body]


def get_app(environ: dict[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
    path = environ.get("PATH_INFO", "")
    metodo = environ.get("REQUEST_METHOD", "GET")
    LOGGER.info(
        "healthcheck_request",
        extra={"evento": "healthcheck", "path": path, "metodo": metodo},
    )
    if path == "/healthz" and metodo == "GET":
        status, headers, body = _respuesta_json("200 OK", {"status": "ok"})
        start_response(status, headers)
        return body

    status, headers, body = _respuesta_json("404 Not Found", {"status": "not_found"})
    start_response(status, headers)
    return body
