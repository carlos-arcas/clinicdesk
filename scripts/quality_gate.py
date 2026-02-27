#!/usr/bin/env python3
"""Quality gate bloqueante para core clínico (Paso 2)."""

from __future__ import annotations

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


def _run_optional_checks() -> int:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists() or "[tool.ruff" not in pyproject.read_text(encoding="utf-8"):
        print("[quality-gate] Ruff no configurado: se omite lint/format.")
        return 0

    ruff = shutil.which("ruff")
    if not ruff:
        print("[quality-gate] Ruff configurado pero no instalado.")
        return 1

    for cmd in ([ruff, "check", "."], [ruff, "format", "--check", "."]):
        print("[quality-gate] Ejecutando:", " ".join(cmd))
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


def main() -> int:
    optional_checks_rc = _run_optional_checks()
    if optional_checks_rc != 0:
        return optional_checks_rc

    pytest_args = ["-q", "-m", "not ui"]
    print("[quality-gate] Ejecutando pytest:", "python -m pytest", " ".join(pytest_args))
    test_rc, tracer = _run_pytest_with_trace(pytest_args)
    if test_rc != 0:
        print(f"[quality-gate] ❌ pytest falló con código {test_rc}.")
        return test_rc

    coverage = _compute_core_coverage(tracer)
    print(f"[quality-gate] Core coverage: {coverage:.2f}% (mínimo {MIN_COVERAGE:.2f}%)")
    if coverage < MIN_COVERAGE:
        print("[quality-gate] ❌ Cobertura de core por debajo del umbral.")
        return 2

    print("[quality-gate] ✅ Gate superado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
