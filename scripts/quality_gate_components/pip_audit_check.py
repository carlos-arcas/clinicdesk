from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from . import config

_LOGGER = logging.getLogger(__name__)


def _load_allowlist_ids(allowlist_path: Path) -> tuple[set[str], int]:
    if not allowlist_path.exists():
        return set(), 0
    try:
        allowlist_data = json.loads(allowlist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _LOGGER.error("[quality-gate] ❌ Allowlist de pip-audit inválida: %s", exc)
        return set(), 6
    ids: set[str] = set()
    for item in allowlist_data.get("vulnerabilidades_permitidas", []):
        cve = str(item.get("id", "")).strip()
        reason = str(item.get("motivo", "")).strip()
        if not cve or not reason:
            _LOGGER.error("[quality-gate] ❌ Entrada inválida en allowlist pip-audit: %s", item)
            return set(), 6
        ids.add(cve.upper())
    return ids, 0


def _pip_audit_offline_flag() -> list[str]:
    if os.getenv("QUALITY_GATE_PIP_AUDIT_SIN_RED") != "1":
        return []
    help_cmd = [sys.executable, "-m", "pip_audit", "--help"]
    help_result = subprocess.run(help_cmd, cwd=config.REPO_ROOT, capture_output=True, text=True, check=False)
    options = f"{help_result.stdout}\n{help_result.stderr}"
    for candidate in ("--no-deps", "--disable-pip"):
        if candidate in options:
            return [candidate]
    return []


def _pip_audit_command(report_path: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "pip_audit",
        "--progress-spinner",
        "off",
        *_pip_audit_offline_flag(),
        "--output",
        str(report_path),
        "--format",
        "columns",
    ]


def _append_process_output(report_path: Path, completed: subprocess.CompletedProcess[str]) -> str:
    content = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    blocks = [content]
    if completed.stdout:
        blocks.append(f"STDOUT:\n{completed.stdout}")
    if completed.stderr:
        blocks.append(f"STDERR:\n{completed.stderr}")
    report_path.write_text("\n\n".join(block for block in blocks if block.strip()) + "\n", encoding="utf-8")
    return f"{completed.stdout or ''}\n{completed.stderr or ''}"


def _missing_module_output(output: str) -> bool:
    return "No module named pip_audit" in output or "ModuleNotFoundError: No module named 'pip_audit'" in output


def _finalize_missing_module(report_path: Path) -> int:
    report_path.write_text(config.MENSAJE_INSTALAR_DEPS_DEV + "\n", encoding="utf-8")
    _LOGGER.error("[quality-gate] ❌ %s", config.MENSAJE_INSTALAR_DEPS_DEV)
    return 6


def _resolve_vulnerability_exit_code(
    found_ids: set[str],
    allowlist_ids: set[str],
    completed: subprocess.CompletedProcess[str],
) -> int:
    non_allowlisted = found_ids - allowlist_ids
    if completed.returncode == 0 or (found_ids and not non_allowlisted):
        if completed.returncode != 0:
            _LOGGER.info("[quality-gate] pip-audit solo reportó vulnerabilidades allowlisted.")
        return 0
    if non_allowlisted:
        _LOGGER.error(
            "[quality-gate] ❌ pip-audit detectó vulnerabilidades no allowlisted: %s",
            ", ".join(sorted(non_allowlisted)),
        )
        return 6
    _LOGGER.error("[quality-gate] ❌ pip-audit detectó vulnerabilidades o no pudo completarse.")
    if "Connection" in completed.stderr or "Temporary failure" in completed.stderr:
        _LOGGER.error(
            "[quality-gate] Fallo de red en pip-audit. Reintenta con red activa o ejecuta en CI con conectividad saliente."
        )
    return 6


def run_pip_audit(
    report_path: Path | None = None,
    allowlist_path: Path | None = None,
    repo_root: Path | None = None,
) -> int:
    report = report_path or config.PIP_AUDIT_REPORT_PATH
    allowlist = allowlist_path or config.PIP_AUDIT_ALLOWLIST_PATH
    root = repo_root or config.REPO_ROOT

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("", encoding="utf-8")

    allowlist_ids, allowlist_rc = _load_allowlist_ids(allowlist)
    if allowlist_rc != 0:
        return allowlist_rc

    command = _pip_audit_command(report)
    _LOGGER.info("[quality-gate] Ejecutando pip-audit.")
    try:
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    except ModuleNotFoundError:
        return _finalize_missing_module(report)

    output = _append_process_output(report, completed)
    if _missing_module_output(output):
        return _finalize_missing_module(report)

    found_ids = {match.upper() for match in re.findall(r"(CVE-\d{4}-\d+|GHSA-[\w-]+)", output)}
    return _resolve_vulnerability_exit_code(found_ids, allowlist_ids, completed)
