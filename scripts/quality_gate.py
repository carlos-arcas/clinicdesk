#!/usr/bin/env python3
"""Quality gate bloqueante para core clínico (Paso 2)."""

from __future__ import annotations

import ast
import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import trace
from pathlib import Path
from typing import Iterable

import pytest
from scripts.structural_gate import run_structural_gate

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
ARTIFACT_SUFFIXES = {".zip", ".db", ".sqlite", ".sqlite3", ".dump", ".bak", ".sqlitedb"}
ARTIFACT_ALLOWLIST = {Path("clinicdesk.zip")}
SCAN_EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "logs"}
MAX_SCAN_BYTES = 1_000_000
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-+/=]{12,}"),
)
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClinicDesk quality gate")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--strict", action="store_true", help="Fail gate on structural violations (default).")
    mode.add_argument("--report-only", action="store_true", help="Generate structural report without blocking.")
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=REPO_ROOT / "scripts" / "quality_thresholds.json",
        help="Path to structural thresholds JSON file.",
    )
    return parser.parse_args()


def _iter_repo_files() -> Iterable[Path]:
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SCAN_EXCLUDE_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        yield path


def _check_forbidden_artifacts() -> int:
    offenders: list[Path] = []
    for file_path in _iter_repo_files():
        rel_path = file_path.relative_to(REPO_ROOT)
        if rel_path in ARTIFACT_ALLOWLIST:
            continue
        if file_path.suffix.lower() in ARTIFACT_SUFFIXES:
            offenders.append(rel_path)
    if not offenders:
        return 0
    _LOGGER.error("[quality-gate] ❌ Se detectaron artefactos prohibidos.")
    for path in sorted(offenders):
        _LOGGER.error("[quality-gate] Artefacto prohibido: %s", path)
    return 4


def _contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _check_secret_patterns() -> int:
    offenders: list[Path] = []
    for file_path in _iter_repo_files():
        try:
            if file_path.stat().st_size > MAX_SCAN_BYTES:
                continue
            text = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if _contains_secret(text):
            offenders.append(file_path.relative_to(REPO_ROOT))

    if not offenders:
        return 0

    _LOGGER.error("[quality-gate] ❌ Se detectaron posibles secretos.")
    for path in sorted(offenders):
        _LOGGER.error("[quality-gate] %s: SECRETO DETECTADO", path)
    return 5


def main() -> int:
    args = _parse_args()
    mode = "report-only" if args.report_only else "strict"

    configure_logging("clinicdesk-quality-gate", REPO_ROOT / "logs", level="INFO", json=False)
    set_run_context("qualitygate")

    no_print_rc = _check_no_print_calls()
    if no_print_rc != 0:
        return no_print_rc

    artifact_rc = _check_forbidden_artifacts()
    if artifact_rc != 0:
        return artifact_rc

    secret_rc = _check_secret_patterns()
    if secret_rc != 0:
        return secret_rc

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

    structural_rc = run_structural_gate(
        repo_root=REPO_ROOT,
        thresholds_path=args.thresholds,
        mode=mode,
        report_path=REPO_ROOT / "docs" / "quality_report.md",
        logger=_LOGGER,
    )
    if structural_rc != 0:
        _LOGGER.error("[quality-gate] ❌ Structural gate falló en modo %s.", mode)
        return structural_rc

    _LOGGER.info("[quality-gate] ✅ Gate superado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
