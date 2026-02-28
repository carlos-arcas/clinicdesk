#!/usr/bin/env python3
"""Quality gate bloqueante para core clínico (Paso 2)."""

from __future__ import annotations

import ast
import logging
import os
import shutil
import subprocess
import sys
import trace
from pathlib import Path
from typing import Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CORE_PATHS = [
    REPO_ROOT / "clinicdesk" / "app" / "domain" / "enums.py",
    REPO_ROOT / "clinicdesk" / "app" / "domain" / "exceptions.py",
    REPO_ROOT / "clinicdesk" / "app" / "application" / "usecases" / "crear_cita.py",
    REPO_ROOT / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "repos_citas.py",
    REPO_ROOT / "clinicdesk" / "app" / "queries" / "citas_queries.py",
]
MIN_COVERAGE = 85.0
PRINT_ALLOWLIST = {Path("tests")}
_LOGGER = logging.getLogger(__name__)

from clinicdesk.app.bootstrap_logging import configure_logging, set_run_context


def _run_optional_checks() -> int:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists() or "[tool.ruff" not in pyproject.read_text(encoding="utf-8"):
        _LOGGER.info("[quality-gate] Ruff no configurado: se omite lint/format.")
        return 0

    ruff = shutil.which("ruff")
    if not ruff:
        _LOGGER.error("[quality-gate] Ruff configurado pero no instalado.")
        return 1

    for cmd in ([ruff, "check", "."], [ruff, "format", "--check", "."]):
        _LOGGER.info("[quality-gate] Ejecutando: %s", " ".join(cmd))
        result = subprocess.run(cmd, cwd=REPO_ROOT)
        if result.returncode != 0:
            return result.returncode
    return 0


def _iter_core_files() -> Iterable[Path]:
    return (path for path in CORE_PATHS if path.exists())


def _run_pytest_with_trace(pytest_args: list[str]) -> tuple[int, trace.Trace]:
    tracer = trace.Trace(count=True, trace=False)
    exit_code = tracer.runfunc(pytest.main, pytest_args)
    return int(exit_code), tracer


def _compute_core_coverage(tracer: trace.Trace) -> float:
    counts = tracer.results().counts
    executable_total = 0
    executed_total = 0

    for file_path in _iter_core_files():
        executable = trace._find_executable_linenos(str(file_path))  # noqa: SLF001
        if not executable:
            continue
        executable_total += len(executable)
        executed_total += sum(1 for line in executable if counts.get((str(file_path), line), 0) > 0)

    if executable_total == 0:
        return 0.0
    return (executed_total / executable_total) * 100.0


def _is_allowlisted(file_path: Path) -> bool:
    rel_path = file_path.relative_to(REPO_ROOT)
    return any(rel_path.parts[: len(root.parts)] == root.parts for root in PRINT_ALLOWLIST)


def _check_no_print_calls() -> int:
    offenders: list[Path] = []
    for file_path in REPO_ROOT.rglob("*.py"):
        if _is_allowlisted(file_path):
            continue
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        has_print_call = any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
            for node in ast.walk(tree)
        )
        if has_print_call:
            offenders.append(file_path)
    if not offenders:
        return 0
    _LOGGER.error("[quality-gate] ❌ Se detectaron print fuera de allowlist.")
    for file_path in offenders:
        _LOGGER.error("[quality-gate] print encontrado en %s", file_path.relative_to(REPO_ROOT))
    return 3


def main() -> int:
    configure_logging("clinicdesk-quality-gate", REPO_ROOT / "logs", level="INFO", json=False)
    set_run_context("qualitygate")

    no_print_rc = _check_no_print_calls()
    if no_print_rc != 0:
        return no_print_rc

    optional_checks_rc = _run_optional_checks()
    if optional_checks_rc != 0:
        return optional_checks_rc

    pytest_args = ["-q", "-m", "not ui"]
    _LOGGER.info("[quality-gate] Ejecutando pytest: python -m pytest %s", " ".join(pytest_args))
    test_rc, tracer = _run_pytest_with_trace(pytest_args)
    if test_rc != 0:
        _LOGGER.error("[quality-gate] ❌ pytest falló con código %s.", test_rc)
        return test_rc

    coverage = _compute_core_coverage(tracer)
    _LOGGER.info("[quality-gate] Core coverage: %.2f%% (mínimo %.2f%%)", coverage, MIN_COVERAGE)
    if coverage < MIN_COVERAGE:
        _LOGGER.error("[quality-gate] ❌ Cobertura de core por debajo del umbral.")
        return 2

    _LOGGER.info("[quality-gate] ✅ Gate superado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
