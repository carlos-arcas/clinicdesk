"""Utilidades para resolver targets Python para Ruff."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def resolver_repo_root(desde: Path | None = None) -> Path:
    """Resuelve la raíz del repositorio para comandos dentro de scripts/."""

    base = desde or Path(__file__).resolve()
    return base.parent.parent


def obtener_targets_python(repo_root: Path) -> list[str]:
    """Devuelve archivos *.py versionados; usa '.' como fallback estable."""

    comando = ["git", "-C", str(repo_root), "ls-files"]
    resultado = subprocess.run(comando, check=False, capture_output=True, text=True)
    if resultado.returncode != 0:
        LOGGER.warning("No se pudo resolver archivos versionados con git; se usa '.' como fallback.")
        return ["."]

    targets = [ruta for bruto in resultado.stdout.splitlines() if (ruta := bruto.strip()).endswith(".py")]
    return targets or ["."]
