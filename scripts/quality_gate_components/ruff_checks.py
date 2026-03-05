from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from scripts._ruff_targets import obtener_targets_python

from . import config

_LOGGER = logging.getLogger(__name__)


def run_required_ruff_checks(repo_root: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    pyproject = root / "pyproject.toml"
    if not pyproject.exists() or "[tool.ruff" not in pyproject.read_text(encoding="utf-8"):
        _LOGGER.error("[quality-gate] ❌ Falta configuración ruff en pyproject.toml.")
        return 1

    python_targets = obtener_targets_python(root)
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
