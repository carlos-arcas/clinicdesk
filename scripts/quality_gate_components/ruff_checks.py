from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from . import config

_LOGGER = logging.getLogger(__name__)


def _resolve_python_targets(root: Path) -> list[str]:
    """Obtiene rutas versionadas de Python para evitar pasar YAML a ruff format."""

    command = ["git", "-C", str(root), "ls-files"]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        _LOGGER.warning("[quality-gate] No se pudo resolver archivos versionados, se usa '.' como fallback.")
        return ["."]

    targets = [path for raw_path in result.stdout.splitlines() if (path := raw_path.strip()).endswith(".py")]
    return targets or ["."]


def run_required_ruff_checks(repo_root: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    pyproject = root / "pyproject.toml"
    if not pyproject.exists() or "[tool.ruff" not in pyproject.read_text(encoding="utf-8"):
        _LOGGER.error("[quality-gate] ❌ Falta configuración ruff en pyproject.toml.")
        return 1

    python_targets = _resolve_python_targets(root)
    commands = (
        [sys.executable, "-m", "ruff", "check", *python_targets],
        [sys.executable, "-m", "ruff", "format", "--check", *python_targets],
    )
    for command in commands:
        _LOGGER.info("[quality-gate] Ejecutando: %s", " ".join(command))
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0
