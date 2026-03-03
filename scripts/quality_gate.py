#!/usr/bin/env python3
"""Quality gate bloqueante para core clínico (Paso 2)."""

from __future__ import annotations

import ast
import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import trace
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from scripts.structural_gate import run_structural_gate

CORE_PATHS = [
    REPO_ROOT / "clinicdesk" / "app" / "domain" / "enums.py",
    REPO_ROOT / "clinicdesk" / "app" / "domain" / "exceptions.py",
    REPO_ROOT / "clinicdesk" / "app" / "application" / "usecases" / "crear_cita.py",
    REPO_ROOT / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "repos_citas.py",
    REPO_ROOT / "clinicdesk" / "app" / "queries" / "citas_queries.py",
]
MIN_COVERAGE = 85.0
COVERAGE_XML_PATH = REPO_ROOT / "docs" / "coverage.xml"
PRINT_ALLOWLIST = {Path("tests")}
ARTIFACT_SUFFIXES = {".zip", ".db", ".sqlite", ".sqlite3", ".dump", ".bak", ".sqlitedb"}
ARTIFACT_ALLOWLIST = {Path("clinicdesk.zip")}
SCAN_EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "logs"}
MAX_SCAN_BYTES = 1_000_000
PIP_AUDIT_REPORT_PATH = REPO_ROOT / "docs" / "pip_audit_report.txt"
PIP_AUDIT_ALLOWLIST_PATH = REPO_ROOT / "docs" / "pip_audit_allowlist.json"
SECRETS_SCAN_REPORT_PATH = REPO_ROOT / "docs" / "secrets_scan_report.txt"
PII_LOGGING_ALLOWLIST_PATH = REPO_ROOT / "docs" / "pii_logging_allowlist.json"
MYPY_SCOPE_PATH = REPO_ROOT / "scripts" / "mypy_scope.txt"
MYPY_REPORT_PATH = REPO_ROOT / "docs" / "mypy_report.txt"
PII_TOKENS = ("dni", "nif", "email", "telefono", "direccion", "historia_clinica")
PII_LOGGING_METHODS = {"debug", "info", "warning", "error", "critical", "exception", "log"}
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?(?=[A-Za-z0-9_\-+/=]*\d)[A-Za-z0-9_\-+/=]{12,}"
    ),
)
_LOGGER = logging.getLogger(__name__)
MENSAJE_INSTALAR_DEPS_DEV = "Instala dependencias dev: pip install -r requirements-dev.txt"

from clinicdesk.app.bootstrap_logging import configure_logging, set_run_context


def _run_required_ruff_checks() -> int:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists() or "[tool.ruff" not in pyproject.read_text(encoding="utf-8"):
        _LOGGER.error("[quality-gate] ❌ Falta configuración ruff en pyproject.toml.")
        return 1

    for cmd in ([sys.executable, "-m", "ruff", "check", "."], [sys.executable, "-m", "ruff", "format", "--check", "."]):
        _LOGGER.info("[quality-gate] Ejecutando: %s", " ".join(cmd))
        result = subprocess.run(cmd, cwd=REPO_ROOT)
        if result.returncode != 0:
            return result.returncode
    return 0


def _load_mypy_scope(scope_path: Path) -> list[str]:
    if not scope_path.exists():
        return []
    paths: list[str] = []
    for line in scope_path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("#"):
            continue
        paths.append(candidate)
    return paths


def _run_mypy_blocking_scope() -> int:
    scope_paths = _load_mypy_scope(MYPY_SCOPE_PATH)
    if not scope_paths:
        _LOGGER.error("[quality-gate] ❌ Scope mypy vacío o inexistente: %s", MYPY_SCOPE_PATH)
        return 9
    command = [sys.executable, "-m", "mypy", *scope_paths]
    _LOGGER.info("[quality-gate] Ejecutando mypy bloqueante sobre scope: %s", " ".join(command))
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return completed.returncode


def _run_mypy_report() -> int:
    MYPY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "mypy", "clinicdesk/app"]
    _LOGGER.info("[quality-gate] Ejecutando mypy report-only: %s", " ".join(command))
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    bloques = [
        "# Reporte mypy (report-only)",
        f"Comando: {' '.join(command)}",
        f"Exit code: {completed.returncode}",
        "",
    ]
    if completed.stdout:
        bloques.extend(["## STDOUT", completed.stdout.rstrip(), ""])
    if completed.stderr:
        bloques.extend(["## STDERR", completed.stderr.rstrip(), ""])
    if not completed.stdout and not completed.stderr:
        bloques.extend(["Sin salida.", ""])
    MYPY_REPORT_PATH.write_text("\n".join(bloques).rstrip() + "\n", encoding="utf-8")
    try:
        report_display = MYPY_REPORT_PATH.relative_to(REPO_ROOT)
    except ValueError:
        report_display = MYPY_REPORT_PATH
    _LOGGER.info("[quality-gate] Reporte mypy generado en %s", report_display)
    return 0


def _run_coverage_report(tracer: trace.Trace, coverage: float) -> int:
    COVERAGE_XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    counts = tracer.results().counts
    package_entries: list[str] = []
    for file_path in _iter_core_files():
        executable = sorted(trace._find_executable_linenos(str(file_path)))  # noqa: SLF001
        if not executable:
            continue
        covered_lines = sum(1 for line in executable if counts.get((str(file_path), line), 0) > 0)
        line_rate = covered_lines / len(executable)
        rel_path = file_path.relative_to(REPO_ROOT).as_posix()
        line_entries = []
        for line in executable:
            hits = 1 if counts.get((str(file_path), line), 0) > 0 else 0
            line_entries.append(f'<line number="{line}" hits="{hits}"/>')
        package_entries.append(
            "".join(
                [
                    f'<class name="{file_path.stem}" filename="{rel_path}" line-rate="{line_rate:.4f}" branch-rate="0">',
                    "<methods/>",
                    "<lines>",
                    *line_entries,
                    "</lines>",
                    "</class>",
                ]
            )
        )

    xml_content = "".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<coverage line-rate="{coverage / 100:.4f}" branch-rate="0" version="clinicdesk-quality-gate">',
            "<sources><source>.</source></sources>",
            '<packages><package name="core" line-rate="0" branch-rate="0"><classes>',
            *package_entries,
            "</classes></package></packages>",
            "</coverage>",
        ]
    )
    COVERAGE_XML_PATH.write_text(xml_content, encoding="utf-8")
    _LOGGER.info("[quality-gate] coverage.xml generado en %s", COVERAGE_XML_PATH.relative_to(REPO_ROOT))
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


def _find_command_path(candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        command_path = shutil.which(candidate)
        if command_path:
            return command_path
    return None


def _run_pip_audit() -> int:
    PIP_AUDIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    flag_sin_red: list[str] = []
    if os.getenv("QUALITY_GATE_PIP_AUDIT_SIN_RED") == "1":
        ayuda = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        opciones = f"{ayuda.stdout}\n{ayuda.stderr}"
        for candidato in ("--no-deps", "--disable-pip"):
            if candidato in opciones:
                flag_sin_red = [candidato]
                break

    command = [
        sys.executable,
        "-m",
        "pip_audit",
        "--progress-spinner",
        "off",
        *flag_sin_red,
        "--output",
        str(PIP_AUDIT_REPORT_PATH),
        "--format",
        "columns",
    ]

    allowlist_ids: set[str] = set()
    if PIP_AUDIT_ALLOWLIST_PATH.exists():
        try:
            allowlist_data = json.loads(PIP_AUDIT_ALLOWLIST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _LOGGER.error("[quality-gate] ❌ Allowlist de pip-audit inválida: %s", exc)
            return 6

        for item in allowlist_data.get("vulnerabilidades_permitidas", []):
            cve = str(item.get("id", "")).strip()
            reason = str(item.get("motivo", "")).strip()
            if not cve or not reason:
                _LOGGER.error("[quality-gate] ❌ Entrada inválida en allowlist pip-audit: %s", item)
                return 6
            allowlist_ids.add(cve.upper())

    _LOGGER.info("[quality-gate] Ejecutando pip-audit.")
    try:
        completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    except ModuleNotFoundError:
        PIP_AUDIT_REPORT_PATH.write_text(MENSAJE_INSTALAR_DEPS_DEV + "\n", encoding="utf-8")
        _LOGGER.error("[quality-gate] ❌ %s", MENSAJE_INSTALAR_DEPS_DEV)
        return 6

    salida_completa = f"{completed.stdout or ''}\n{completed.stderr or ''}"
    if "No module named pip_audit" in salida_completa or "ModuleNotFoundError: No module named 'pip_audit'" in salida_completa:
        PIP_AUDIT_REPORT_PATH.write_text(MENSAJE_INSTALAR_DEPS_DEV + "\n", encoding="utf-8")
        _LOGGER.error("[quality-gate] ❌ %s", MENSAJE_INSTALAR_DEPS_DEV)
        return 6

    bloques_reporte = [PIP_AUDIT_REPORT_PATH.read_text(encoding="utf-8") if PIP_AUDIT_REPORT_PATH.exists() else ""]
    if completed.stdout:
        bloques_reporte.append(f"STDOUT:\n{completed.stdout}")
    if completed.stderr:
        bloques_reporte.append(f"STDERR:\n{completed.stderr}")
    PIP_AUDIT_REPORT_PATH.write_text("\n\n".join(b for b in bloques_reporte if b.strip()) + "\n", encoding="utf-8")

    ids_detectados = {match.upper() for match in re.findall(r"(CVE-\d{4}-\d+|GHSA-[\w-]+)", salida_completa)}
    ids_no_permitidos = ids_detectados - allowlist_ids

    if completed.returncode == 0:
        return 0

    if ids_detectados and not ids_no_permitidos:
        _LOGGER.info("[quality-gate] pip-audit solo reportó vulnerabilidades allowlisted.")
        return 0

    if ids_no_permitidos:
        _LOGGER.error(
            "[quality-gate] ❌ pip-audit detectó vulnerabilidades no allowlisted: %s",
            ", ".join(sorted(ids_no_permitidos)),
        )
        return 6

    _LOGGER.error("[quality-gate] ❌ pip-audit detectó vulnerabilidades o no pudo completarse.")
    if "Connection" in completed.stderr or "Temporary failure" in completed.stderr:
        _LOGGER.error(
            "[quality-gate] Fallo de red en pip-audit. Reintenta con red activa o ejecuta en CI con conectividad saliente."
        )
    return 6


def _run_secrets_scan() -> int:
    scanner = _find_command_path(("gitleaks",))
    if scanner is None:
        SECRETS_SCAN_REPORT_PATH.write_text(
            "No se encontró gitleaks en PATH.\n"
            "Instalación local sugerida (Ubuntu): sudo apt-get install -y gitleaks\n"
            "CI debe instalar gitleaks antes de ejecutar python -m scripts.gate_pr\n",
            encoding="utf-8",
        )
        _LOGGER.error("[quality-gate] ❌ Falta gitleaks en PATH. Revisa docs/ci_quality_gate.md para instalación.")
        return 7

    command = [
        scanner,
        "detect",
        "--source",
        str(REPO_ROOT),
        "--no-git",
        "--report-format",
        "json",
        "--report-path",
        str(SECRETS_SCAN_REPORT_PATH),
    ]
    _LOGGER.info("[quality-gate] Ejecutando escaneo de secretos con gitleaks.")
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    report_tail = "\n\nSTDOUT:\n" + (completed.stdout or "") + "\nSTDERR:\n" + (completed.stderr or "")
    if SECRETS_SCAN_REPORT_PATH.exists():
        SECRETS_SCAN_REPORT_PATH.write_text(
            SECRETS_SCAN_REPORT_PATH.read_text(encoding="utf-8") + report_tail,
            encoding="utf-8",
        )
    else:
        SECRETS_SCAN_REPORT_PATH.write_text(report_tail, encoding="utf-8")
    if completed.returncode == 0:
        return 0
    _LOGGER.error("[quality-gate] ❌ gitleaks detectó secretos o falló la ejecución.")
    return 7


def _load_pii_allowlist() -> dict[str, str]:
    if not PII_LOGGING_ALLOWLIST_PATH.exists():
        return {}
    try:
        payload = json.loads(PII_LOGGING_ALLOWLIST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _LOGGER.error("[quality-gate] ❌ Allowlist de PII inválida: %s", exc)
        return {}
    allowlist_entries = payload.get("entradas", [])
    mapping: dict[str, str] = {}
    for entry in allowlist_entries:
        clave = str(entry.get("clave", "")).strip()
        motivo = str(entry.get("motivo", "")).strip()
        if clave and motivo:
            mapping[clave] = motivo
    return mapping


def _extract_string_literals(node: ast.AST) -> list[str]:
    literals: list[str] = []
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        literals.append(node.value)
    if isinstance(node, ast.JoinedStr):
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                literals.append(value.value)
    return literals


def _check_pii_logging_guardrail() -> int:
    allowlist = _load_pii_allowlist()
    offenders: list[str] = []
    for file_path in REPO_ROOT.rglob("*.py"):
        rel_path = file_path.relative_to(REPO_ROOT)
        if rel_path.parts and rel_path.parts[0] in {"docs"}:
            continue
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in PII_LOGGING_METHODS:
                continue
            for argument in node.args:
                for literal in _extract_string_literals(argument):
                    lowered = literal.lower()
                    matched_tokens = [token for token in PII_TOKENS if token in lowered]
                    if not matched_tokens:
                        continue
                    clave = f"{rel_path}:{node.lineno}:{','.join(matched_tokens)}"
                    if clave in allowlist:
                        continue
                    offenders.append(clave)
    if not offenders:
        return 0
    _LOGGER.error("[quality-gate] ❌ Guardrail PII/logging detectó mensajes hardcodeados sensibles.")
    for offender in sorted(offenders):
        _LOGGER.error("[quality-gate] %s", offender)
    return 8


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

    pip_audit_rc = _run_pip_audit()
    if pip_audit_rc != 0:
        return pip_audit_rc

    secrets_scan_rc = _run_secrets_scan()
    if secrets_scan_rc != 0:
        return secrets_scan_rc

    pii_logging_rc = _check_pii_logging_guardrail()
    if pii_logging_rc != 0:
        return pii_logging_rc

    ruff_rc = _run_required_ruff_checks()
    if ruff_rc != 0:
        return ruff_rc

    mypy_scope_rc = _run_mypy_blocking_scope()
    if mypy_scope_rc != 0:
        _LOGGER.error("[quality-gate] ❌ mypy bloqueante falló sobre scripts/mypy_scope.txt.")
        return mypy_scope_rc

    mypy_report_rc = _run_mypy_report()
    if mypy_report_rc != 0:
        _LOGGER.error("[quality-gate] ❌ Falló la generación de docs/mypy_report.txt.")
        return mypy_report_rc

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

    coverage_report_rc = _run_coverage_report(tracer=tracer, coverage=coverage)
    if coverage_report_rc != 0:
        _LOGGER.error("[quality-gate] ❌ Falló la generación de coverage.xml en docs/.")
        return coverage_report_rc

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
