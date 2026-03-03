from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from . import config

_LOGGER = logging.getLogger(__name__)


def load_mypy_scope(scope_path: Path) -> list[str]:
    if not scope_path.exists():
        return []
    paths: list[str] = []
    for line in scope_path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if candidate and not candidate.startswith("#"):
            paths.append(candidate)
    return paths


def run_mypy_blocking_scope(scope_path: Path | None = None, repo_root: Path | None = None) -> int:
    scope = scope_path or config.MYPY_SCOPE_PATH
    root = repo_root or config.REPO_ROOT
    scope_paths = load_mypy_scope(scope)
    if not scope_paths:
        _LOGGER.error("[quality-gate] ❌ Scope mypy vacío o inexistente: %s", scope)
        return 9
    command = [sys.executable, "-m", "mypy", *scope_paths]
    _LOGGER.info("[quality-gate] Ejecutando mypy bloqueante sobre scope: %s", " ".join(command))
    return subprocess.run(command, cwd=root, check=False).returncode


def run_mypy_report(report_path: Path | None = None, repo_root: Path | None = None) -> int:
    report = report_path or config.MYPY_REPORT_PATH
    root = repo_root or config.REPO_ROOT
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("", encoding="utf-8")

    command = [sys.executable, "-m", "mypy", "clinicdesk/app"]
    _LOGGER.info("[quality-gate] Ejecutando mypy report-only: %s", " ".join(command))
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)

    blocks = ["# Reporte mypy (report-only)", f"Comando: {' '.join(command)}", f"Exit code: {completed.returncode}", ""]
    if completed.stdout:
        blocks.extend(["## STDOUT", completed.stdout.rstrip(), ""])
    if completed.stderr:
        blocks.extend(["## STDERR", completed.stderr.rstrip(), ""])
    if not completed.stdout and not completed.stderr:
        blocks.extend(["Sin salida.", ""])
    report.write_text("\n".join(blocks).rstrip() + "\n", encoding="utf-8")

    try:
        display = report.relative_to(root)
    except ValueError:
        display = report
    _LOGGER.info("[quality-gate] Reporte mypy generado en %s", display)
    return 0
