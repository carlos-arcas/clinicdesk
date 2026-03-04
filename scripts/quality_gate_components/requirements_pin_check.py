from __future__ import annotations

import logging
import re
from pathlib import Path

from . import config

_LOGGER = logging.getLogger(__name__)
_PATRON_PIN = re.compile(r"^[A-Za-z0-9_.\-\[\]]+==[^\s]+$")


def _linea_ignorable(linea: str) -> bool:
    contenido = linea.strip()
    return not contenido or contenido.startswith("#")


def _linea_opcion(linea: str) -> bool:
    contenido = linea.strip()
    return contenido.startswith(("-", "--")) or " --hash=" in contenido


def linea_esta_pinneada(linea: str) -> bool:
    contenido = linea.strip()
    if _linea_ignorable(contenido) or _linea_opcion(contenido):
        return True
    return bool(_PATRON_PIN.match(contenido))


def validar_requirements_pinneados(requirements_path: Path) -> list[tuple[int, str]]:
    errores: list[tuple[int, str]] = []
    for numero_linea, linea in enumerate(requirements_path.read_text(encoding="utf-8").splitlines(), start=1):
        if linea_esta_pinneada(linea):
            continue
        errores.append((numero_linea, linea.strip()))
    return errores


def check_requirements_pinneados(repo_root: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    offenders: dict[str, list[tuple[int, str]]] = {}
    for nombre in ("requirements.txt", "requirements-dev.txt"):
        ruta = root / nombre
        if not ruta.exists():
            _LOGGER.error("[quality-gate] ❌ Falta archivo obligatorio: %s", nombre)
            return 9
        errores = validar_requirements_pinneados(ruta)
        if errores:
            offenders[nombre] = errores

    if not offenders:
        return 0

    _LOGGER.error("[quality-gate] ❌ Requirements sin pin estricto (usar ==).")
    for nombre, errores in offenders.items():
        for numero_linea, contenido in errores:
            _LOGGER.error("[quality-gate] %s:%s -> %s", nombre, numero_linea, contenido)
    return 9
