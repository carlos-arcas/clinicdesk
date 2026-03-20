from __future__ import annotations

import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from scripts._ruff_targets import obtener_targets_python

from . import config
from .toolchain import cargar_toolchain_esperado

_LOGGER = logging.getLogger(__name__)
RUTA_ARTEFACTO_DIFF_RUFF = Path("docs/ruff_format_diff.txt")
DELIMITADOR_INICIO_DIFF = "BEGIN RUFF FORMAT DIFF"
DELIMITADOR_FIN_DIFF = "END RUFF FORMAT DIFF"
MAX_LINEAS_DIFF_HEAD = 200
MAX_LINEAS_DIFF_TAIL = 50
PATRON_VERSION_RUFF = re.compile(r"ruff\s+(?P<version>\S+)")
PATRON_WOULD_REFORMAT = re.compile(r"^Would reformat:\s+(?P<ruta>.+)$")


def _loggear_version_ruff(root: Path) -> tuple[int, str]:
    comando = [sys.executable, "-m", "ruff", "--version"]
    _LOGGER.info("[quality-gate] Ejecutando: %s", " ".join(comando))
    resultado = subprocess.run(comando, cwd=root, check=False, capture_output=True, text=True)
    salida = resultado.stdout.strip() or resultado.stderr.strip()
    if salida:
        _LOGGER.info("[quality-gate] ruff_version=%s", salida)
    if resultado.returncode != 0:
        _LOGGER.error("[quality-gate] ❌ No se pudo obtener la versión de Ruff.")
    return resultado.returncode, salida


def _obtener_version_ruff_pinneada(root: Path) -> str | None:
    try:
        return cargar_toolchain_esperado(root).version_esperada("ruff")
    except Exception as exc:
        _LOGGER.error("[quality-gate] ❌ No se pudo cargar la fuente de verdad del tooling: %s", exc)
        return None


def _extraer_version_ruff_instalada(salida_version: str) -> str | None:
    match = PATRON_VERSION_RUFF.search(salida_version)
    if not match:
        _LOGGER.error("[quality-gate] ❌ No se pudo parsear la versión de Ruff: %s", salida_version)
        return None
    return match.group("version")


def _validar_version_ruff(root: Path, salida_version: str) -> int:
    version_pinneada = _obtener_version_ruff_pinneada(root)
    if version_pinneada is None:
        return 1

    version_instalada = _extraer_version_ruff_instalada(salida_version)
    if version_instalada is None:
        return 1

    if version_instalada != version_pinneada:
        _LOGGER.error(
            "[quality-gate] ❌ Ruff desalineado con CI/local lock: instalado=%s pin=%s. "
            "Instala dependencias con `python -m pip install -r requirements-dev.txt` "
            "antes de ejecutar el gate.",
            version_instalada,
            version_pinneada,
        )
        return 1

    _LOGGER.info("[quality-gate] Ruff alineado con pin de requirements-dev.txt: %s", version_pinneada)
    return 0


def _ejecutar_comando_ruff(root: Path, comando: Sequence[str]) -> int:
    _LOGGER.info("[quality-gate] Ejecutando: %s", " ".join(comando))
    resultado = subprocess.run(comando, cwd=root, check=False)
    return resultado.returncode


def _ejecutar_comando_ruff_con_salida(root: Path, comando: Sequence[str]) -> subprocess.CompletedProcess[str]:
    _LOGGER.info("[quality-gate] Ejecutando: %s", " ".join(comando))
    return subprocess.run(comando, cwd=root, check=False, capture_output=True, text=True)


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


def _construir_reporte_fallback(stdout: str, stderr: str) -> str:
    return "\n".join(
        [
            "comando: no-ejecutado (sin archivos parseables de 'Would reformat:')",
            "returncode: no-ejecutado",
            "motivo: Ruff format --check falló, pero no se pudieron extraer rutas concretas para --diff.",
            "--- salida format --check stdout ---",
            stdout or "(vacío)",
            "--- salida format --check stderr ---",
            stderr or "(vacío)",
            "",
        ]
    )


def _extraer_archivos_reformateables(stdout: str, stderr: str) -> list[str]:
    archivos: list[str] = []
    vistos: set[str] = set()
    for linea in [*stdout.splitlines(), *stderr.splitlines()]:
        match = PATRON_WOULD_REFORMAT.match(linea.strip())
        if not match:
            continue
        ruta = match.group("ruta").strip()
        if ruta in vistos:
            continue
        vistos.add(ruta)
        archivos.append(ruta)
    return archivos


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


def _diagnosticar_fallo_formato(root: Path, stdout_format_check: str, stderr_format_check: str) -> None:
    archivos_reales = _extraer_archivos_reformateables(stdout_format_check, stderr_format_check)
    if not archivos_reales:
        _LOGGER.warning(
            "ruff_format_diff_sin_targets_parseables",
            extra={"motivo": "no_would_reformat", "ruta": str(root / RUTA_ARTEFACTO_DIFF_RUFF)},
        )
        _persistir_diff_ruff(root, _construir_reporte_fallback(stdout_format_check, stderr_format_check))
        _imprimir_diff_en_logs(root)
        return

    comando = [sys.executable, "-m", "ruff", "format", "--diff", *archivos_reales]
    _LOGGER.info(
        "ruff_format_diff_ejecucion",
        extra={"comando": " ".join(comando), "targets": archivos_reales},
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

    version_code, version_output = _loggear_version_ruff(root)
    if version_code != 0:
        return version_code
    version_match_rc = _validar_version_ruff(root, version_output)
    if version_match_rc != 0:
        return version_match_rc

    python_targets = obtener_targets_python(root)
    check_command = [sys.executable, "-m", "ruff", "check", *python_targets]
    check_rc = _ejecutar_comando_ruff(root, check_command)
    if check_rc != 0:
        return check_rc

    format_command = [sys.executable, "-m", "ruff", "format", "--check", *python_targets]
    resultado_format_check = _ejecutar_comando_ruff_con_salida(root, format_command)
    if resultado_format_check.returncode != 0:
        _LOGGER.error("ruff_format_check_fallo", extra={"returncode": resultado_format_check.returncode})
        _diagnosticar_fallo_formato(root, resultado_format_check.stdout, resultado_format_check.stderr)
        return resultado_format_check.returncode
    return 0
