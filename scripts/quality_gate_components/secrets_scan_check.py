from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Callable

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


def _resolver_repo_root(repo_root: Path | None) -> Path:
    return repo_root or config.REPO_ROOT


def _resolver_report_path(report_path: Path | None) -> Path:
    return report_path or config.SECRETS_SCAN_REPORT_PATH


def _gitleaks_disponible(command_finder: Callable[[tuple[str, ...]], str | None] | None = None) -> bool:
    finder = command_finder or find_command_path
    return finder(("gitleaks",)) is not None


def _resolver_argumento_reporte(repo_root: Path, report_path: Path) -> str:
    try:
        return str(report_path.relative_to(repo_root))
    except ValueError:
        return str(report_path)


def _contar_hallazgos_desde_reporte(report_path: Path) -> int:
    if not report_path.exists():
        return -1
    try:
        parsed = json.loads(report_path.read_text(encoding="utf-8") or "[]")
    except json.JSONDecodeError:
        return -1
    return len(parsed) if isinstance(parsed, list) else -1


def _ejecutar_gitleaks(repo_root: Path, report_path: Path) -> tuple[int, int]:
    comando = [
        "gitleaks",
        "detect",
        "--source",
        ".",
        "--config",
        ".gitleaks.toml",
        "--report-format",
        "json",
        "--report-path",
        _resolver_argumento_reporte(repo_root, report_path),
    ]
    resultado = subprocess.run(comando, cwd=repo_root, capture_output=True, text=True, check=False)
    _normalize_json_report(report_path, resultado)
    hallazgos = _contar_hallazgos_desde_reporte(report_path)
    return resultado.returncode, hallazgos


def _ejecutar_fallback(repo_root: Path, report_path: Path) -> tuple[int, int]:
    hallazgos = scan_repo(repo_root)
    report_path.write_text(render_report(hallazgos), encoding="utf-8")
    return (7 if hallazgos else 0), len(hallazgos)


def _asegurar_reporte_existe(report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not report_path.exists():
        report_path.write_text("[]\n", encoding="utf-8")


def _log_resultado(metodo: str, hallazgos: int) -> None:
    _LOGGER.info("[quality-gate] secrets_scan metodo=%s hallazgos=%s", metodo, hallazgos)


def _ejecutar_segun_metodo(
    root: Path,
    report: Path,
    command_finder: Callable[[tuple[str, ...]], str | None] | None,
) -> tuple[str, int, int]:
    if _gitleaks_disponible(command_finder):
        codigo, hallazgos = _ejecutar_gitleaks(root, report)
        return "gitleaks", codigo, hallazgos
    codigo, hallazgos = _ejecutar_fallback(root, report)
    return "fallback", codigo, hallazgos


def _log_error_scan(metodo: str) -> None:
    mensajes = {
        "gitleaks": "[quality-gate] ❌ gitleaks detectó secretos o falló la ejecución.",
        "fallback": "[quality-gate] ❌ Escaneo fallback detectó posibles secretos.",
    }
    _LOGGER.error(mensajes[metodo])


def run_secrets_scan(
    report_path: Path | None = None,
    repo_root: Path | None = None,
    command_finder=None,
) -> int:
    # CC alto previo por orquestación con múltiples ramas (gitleaks/fallback + rutas + logging + reporte).
    root = _resolver_repo_root(repo_root)
    report = _resolver_report_path(report_path)
    _asegurar_reporte_existe(report)
    report.write_text("[]\n", encoding="utf-8")

    metodo, codigo, hallazgos = _ejecutar_segun_metodo(root, report, command_finder)
    _log_resultado(metodo, hallazgos)
    if codigo == 0:
        return 0
    _log_error_scan(metodo)
    return 7
