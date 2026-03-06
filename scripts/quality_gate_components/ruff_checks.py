from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from scripts._ruff_targets import obtener_targets_python

from . import config

_LOGGER = logging.getLogger(__name__)
RUTA_ARTEFACTO_DIFF_RUFF = Path("docs/ruff_format_diff.txt")
DELIMITADOR_INICIO_DIFF = "BEGIN RUFF FORMAT DIFF"
DELIMITADOR_FIN_DIFF = "END RUFF FORMAT DIFF"
MAX_LINEAS_DIFF_HEAD = 200
MAX_LINEAS_DIFF_TAIL = 50
TARGETS_DIFF_RUFF = (
    "tests/test_checklist_funcional_contract.py",
    "tests/test_quality_thresholds_contract.py",
)


def _loggear_version_ruff(root: Path) -> int:
    comando = [sys.executable, "-m", "ruff", "--version"]
    _LOGGER.info("[quality-gate] Ejecutando: %s", " ".join(comando))
    resultado = subprocess.run(comando, cwd=root, check=False, capture_output=True, text=True)
    salida = resultado.stdout.strip() or resultado.stderr.strip()
    if salida:
        _LOGGER.info("[quality-gate] ruff_version=%s", salida)
    if resultado.returncode != 0:
        _LOGGER.error("[quality-gate] ❌ No se pudo obtener la versión de Ruff.")
    return resultado.returncode


def _ejecutar_comando_ruff(root: Path, comando: Sequence[str]) -> int:
    _LOGGER.info("[quality-gate] Ejecutando: %s", " ".join(comando))
    resultado = subprocess.run(comando, cwd=root, check=False)
    return resultado.returncode


def _persistir_diff_ruff(root: Path, contenido: str) -> None:
    ruta = root / RUTA_ARTEFACTO_DIFF_RUFF
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    _LOGGER.info(
        "ruff_format_diff_guardado",
        extra={"ruta": str(ruta), "tamano": len(contenido)},
    )


def _construir_reporte_diff(comando: Sequence[str], retorno: str, stdout: str, stderr: str) -> str:
    return "\n".join(
        [
            f"comando: {' '.join(comando)}",
            f"returncode: {retorno}",
            "--- stdout ---",
            stdout or "(vacío)",
            "--- stderr ---",
            stderr or "(vacío)",
            "",
        ]
    )


def _persistir_error_diff(root: Path, comando: Sequence[str], exc: OSError) -> None:
    contenido = _construir_reporte_diff(comando, "no-ejecutado", "", f"No se pudo ejecutar Ruff diff: {exc}")
    _persistir_diff_ruff(root, contenido)
    _LOGGER.error(
        "ruff_format_diff_error_ejecucion",
        extra={"error": str(exc), "ruta": str(root / RUTA_ARTEFACTO_DIFF_RUFF)},
    )


def _construir_diff_para_logs(contenido: str) -> str:
    lineas = contenido.splitlines()
    total = len(lineas)
    if total <= MAX_LINEAS_DIFF_HEAD + MAX_LINEAS_DIFF_TAIL:
        return "\n".join(lineas)

    head = lineas[:MAX_LINEAS_DIFF_HEAD]
    tail = lineas[-MAX_LINEAS_DIFF_TAIL:]
    recortadas = total - (MAX_LINEAS_DIFF_HEAD + MAX_LINEAS_DIFF_TAIL)
    marcador = f"... diff truncado: {recortadas} líneas omitidas ..."
    return "\n".join([*head, marcador, *tail])


def _imprimir_diff_en_logs(root: Path) -> None:
    ruta = root / RUTA_ARTEFACTO_DIFF_RUFF
    if not ruta.exists():
        _LOGGER.warning("ruff_format_diff_no_encontrado", extra={"ruta": str(ruta)})
        return

    contenido = ruta.read_text(encoding="utf-8", errors="ignore")
    diff = _construir_diff_para_logs(contenido)
    _LOGGER.info(DELIMITADOR_INICIO_DIFF)
    _LOGGER.info(diff)
    _LOGGER.info(DELIMITADOR_FIN_DIFF)


def _diagnosticar_fallo_formato(root: Path) -> None:
    comando = [sys.executable, "-m", "ruff", "format", "--diff", *TARGETS_DIFF_RUFF]
    _LOGGER.info(
        "ruff_format_diff_ejecucion",
        extra={"comando": " ".join(comando), "targets": list(TARGETS_DIFF_RUFF)},
    )
    try:
        resultado = subprocess.run(comando, cwd=root, check=False, capture_output=True, text=True)
    except OSError as exc:
        _persistir_error_diff(root, comando, exc)
        _imprimir_diff_en_logs(root)
        return

    contenido = _construir_reporte_diff(
        comando, str(resultado.returncode), resultado.stdout.strip(), resultado.stderr.strip()
    )
    _persistir_diff_ruff(root, contenido)
    _imprimir_diff_en_logs(root)
    if resultado.returncode in (0, 1):
        _LOGGER.info(
            "ruff_format_diff_ok",
            extra={"returncode": resultado.returncode, "ruta": str(root / RUTA_ARTEFACTO_DIFF_RUFF)},
        )
        return
    _LOGGER.error(
        "ruff_format_diff_fallo",
        extra={"returncode": resultado.returncode, "ruta": str(root / RUTA_ARTEFACTO_DIFF_RUFF)},
    )


def run_required_ruff_checks(repo_root: Path | None = None) -> int:
    root = repo_root or config.REPO_ROOT
    pyproject = root / "pyproject.toml"
    if not pyproject.exists() or "[tool.ruff" not in pyproject.read_text(encoding="utf-8"):
        _LOGGER.error("[quality-gate] ❌ Falta configuración ruff en pyproject.toml.")
        return 1

    version_code = _loggear_version_ruff(root)
    if version_code != 0:
        return version_code

    python_targets = obtener_targets_python(root)
    check_command = [sys.executable, "-m", "ruff", "check", *python_targets]
    check_rc = _ejecutar_comando_ruff(root, check_command)
    if check_rc != 0:
        return check_rc

    format_command = [sys.executable, "-m", "ruff", "format", "--check", *python_targets]
    format_rc = _ejecutar_comando_ruff(root, format_command)
    if format_rc != 0:
        _LOGGER.error("ruff_format_check_fallo", extra={"returncode": format_rc})
        _diagnosticar_fallo_formato(root)
        return format_rc
    return 0
