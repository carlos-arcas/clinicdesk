from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from . import config

_LOGGER = logging.getLogger(__name__)


def find_command_path(candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        command_path = shutil.which(candidate)
        if command_path:
            return command_path
    return None


def _write_missing_tool_report(report_path: Path) -> None:
    report_path.write_text(
        json.dumps(
            {
                "error": "No se encontró gitleaks en PATH",
                "instalacion_sugerida": "sudo apt-get install -y gitleaks",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _normalize_json_report(report_path: Path, completed: subprocess.CompletedProcess[str]) -> None:
    if not report_path.exists():
        report_path.write_text("[]\n", encoding="utf-8")
        return
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8") or "[]")
    except json.JSONDecodeError:
        payload = []
    if completed.returncode == 0 and not isinstance(payload, list):
        report_path.write_text("[]\n", encoding="utf-8")


def run_secrets_scan(
    report_path: Path | None = None,
    repo_root: Path | None = None,
    command_finder=None,
) -> int:
    report = report_path or config.SECRETS_SCAN_REPORT_PATH
    root = repo_root or config.REPO_ROOT
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("[]\n", encoding="utf-8")

    finder = command_finder or find_command_path
    scanner = finder(("gitleaks",))
    if scanner is None:
        _write_missing_tool_report(report)
        _LOGGER.error("[quality-gate] ❌ Falta gitleaks en PATH. Revisa docs/ci_quality_gate.md para instalación.")
        return 7

    command = [
        scanner,
        "detect",
        "--source",
        ".",
        "--config",
        ".gitleaks.toml",
        "--report-format",
        "json",
        "--report-path",
        "docs/secrets_scan_report.txt",
    ]
    _LOGGER.info("[quality-gate] Ejecutando escaneo de secretos con gitleaks.")
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    _normalize_json_report(report, completed)
    if completed.returncode == 0:
        return 0
    _LOGGER.error("[quality-gate] ❌ gitleaks detectó secretos o falló la ejecución.")
    return 7
