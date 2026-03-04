from __future__ import annotations

import logging
from pathlib import Path

from . import config

_LOGGER = logging.getLogger(__name__)

_ARCHIVOS_REQUERIMIENTOS = ("requirements.txt", "requirements-dev.txt")
_PREFIJOS_PERMITIDOS = ("-r", "--requirement", "--index-url", "--extra-index-url", "--trusted-host", "--find-links")


def linea_requerimiento_pinneada(linea: str) -> bool:
    contenido = linea.strip()
    if not contenido or contenido.startswith("#"):
        return True
    if contenido.startswith(_PREFIJOS_PERMITIDOS):
        return True
    if " @ " in contenido:
        return True
    return "==" in contenido


def recolectar_lineas_no_pinneadas(path: Path) -> list[tuple[int, str]]:
    no_pinneadas: list[tuple[int, str]] = []
    for numero, linea in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not linea_requerimiento_pinneada(linea):
            no_pinneadas.append((numero, linea.strip()))
    return no_pinneadas


def check_requirements_pinneados(repo_root: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    errores: list[tuple[Path, int, str]] = []

    for nombre_archivo in _ARCHIVOS_REQUERIMIENTOS:
        path = root / nombre_archivo
        if not path.exists():
            _LOGGER.error("[quality-gate] ❌ Falta archivo requerido: %s", nombre_archivo)
            return 9
        for numero, linea in recolectar_lineas_no_pinneadas(path):
            errores.append((path.relative_to(root), numero, linea))

    if not errores:
        return 0

    _LOGGER.error("[quality-gate] ❌ Se detectaron dependencias no pinneadas (usar '==').")
    for path, numero, linea in errores:
        _LOGGER.error("[quality-gate] %s:%s -> %s", path, numero, linea)
    return 9
