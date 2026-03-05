from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from . import config
from .secrets_scan_fallback import render_report, scan_repo

_LOGGER = logging.getLogger(__name__)


def find_command_path(candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        command_path = shutil.which(candidate)
        if command_path:
            return command_path
    return None


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
    # gitleaks puede no existir en entornos restringidos locales.
    # En ese caso mantenemos el guardrail con un escaneo fallback en Python.
    if scanner is None:
        hallazgos = scan_repo(root)
        report.write_text(render_report(hallazgos), encoding="utf-8")
        _LOGGER.info(
            "[quality-gate] secrets_scan metodo=fallback hallazgos=%s",
            len(hallazgos),
        )
        if hallazgos:
            _LOGGER.error("[quality-gate] ❌ Escaneo fallback detectó posibles secretos.")
            return 7
        return 0

    report_argument = str(report)
    try:
        report_argument = str(report.relative_to(root))
    except ValueError:
        report_argument = str(report)

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
        report_argument,
    ]
    _LOGGER.info("[quality-gate] secrets_scan metodo=gitleaks")
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    _normalize_json_report(report, completed)
    findings = -1
    if report.exists():
        try:
            parsed = json.loads(report.read_text(encoding="utf-8") or "[]")
            findings = len(parsed) if isinstance(parsed, list) else -1
        except json.JSONDecodeError:
            findings = -1
    _LOGGER.info("[quality-gate] secrets_scan metodo=gitleaks hallazgos=%s", findings)
    if completed.returncode == 0:
        return 0
    _LOGGER.error("[quality-gate] ❌ gitleaks detectó secretos o falló la ejecución.")
    return 7
