from __future__ import annotations

import json
import importlib.util
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from . import config

_LOGGER = logging.getLogger(__name__)
RC_DEPENDENCIA_FALTANTE = 2
_MENSAJE_COVERAGE_FALTANTE = (
    "[quality-gate] Falta dependencia 'coverage'. Ejecuta: pip install -r requirements-dev.txt (o scripts/setup.*)."
)


def iter_core_files(core_paths: list[Path] | None = None) -> Iterable[Path]:
    return (path for path in (core_paths or config.CORE_PATHS) if path.exists())


def _build_pytest_env() -> dict[str, str]:
    entorno = os.environ.copy()
    entorno["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    entorno["PYTEST_ADDOPTS"] = ""
    return entorno


def _run_cmd(comando: list[str], *, env: dict[str, str]) -> int:
    return subprocess.run(comando, check=False, env=env).returncode


def _coverage_disponible() -> bool:
    return importlib.util.find_spec("coverage") is not None


def run_pytest_with_coverage(pytest_args: list[str], env: dict[str, str] | None = None) -> int:
    # Root cause CI: pytest-qt entraba por autoload de entrypoints aunque el selector fuera "not ui".
    if not _coverage_disponible():
        _LOGGER.error(_MENSAJE_COVERAGE_FALTANTE)
        return RC_DEPENDENCIA_FALTANTE

    entorno = env or _build_pytest_env()
    _run_cmd([sys.executable, "-m", "coverage", "erase"], env=entorno)
    comando = [sys.executable, "-m", "coverage", "run", "-m", "pytest", *pytest_args]
    return _run_cmd(comando, env=entorno)


def run_pytest_core_con_coverage(pytest_args: list[str]) -> float | None:
    entorno = _build_pytest_env()
    if run_pytest_with_coverage(pytest_args, env=entorno) != 0:
        return None
    if run_coverage_report(env=entorno) != 0:
        return None
    if run_coverage_json(env=entorno) != 0:
        return None
    return compute_core_coverage()


def compute_core_coverage(core_paths: list[Path] | None = None, reporte_json: Path | None = None) -> float:
    json_path = reporte_json or config.REPO_ROOT / "docs" / "coverage.json"
    if not json_path.exists():
        return 0.0

    contenido = json.loads(json_path.read_text(encoding="utf-8"))
    archivos = contenido.get("files", {})
    ejecutables = 0
    ejecutadas = 0
    for core_path in iter_core_files(core_paths=core_paths):
        resumen = _buscar_resumen_archivo(archivos, core_path)
        if not resumen:
            continue
        ejecutables += int(resumen.get("num_statements", 0))
        ejecutadas += int(resumen.get("covered_lines", 0))

    if ejecutables == 0:
        return 0.0
    return (ejecutadas / ejecutables) * 100.0


def _buscar_resumen_archivo(archivos: dict[str, dict], core_path: Path) -> dict | None:
    objetivo = core_path.resolve().as_posix()
    relativo = core_path.relative_to(config.REPO_ROOT).as_posix()
    for nombre, datos in archivos.items():
        normalizado = Path(nombre).resolve().as_posix() if Path(nombre).is_absolute() else nombre
        if normalizado == objetivo or nombre.endswith(relativo):
            return datos.get("summary", {})
    return None


def run_coverage_report(coverage_xml_path: Path | None = None, env: dict[str, str] | None = None) -> int:
    xml_path = coverage_xml_path or config.COVERAGE_XML_PATH
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    comando = [sys.executable, "-m", "coverage", "xml", "-o", str(xml_path)]
    rc = subprocess.run(comando, check=False, env=env).returncode
    if rc == 0:
        _LOGGER.info("[quality-gate] coverage.xml generado en %s", xml_path.relative_to(config.REPO_ROOT))
    return rc


def run_coverage_json(coverage_json_path: Path | None = None, env: dict[str, str] | None = None) -> int:
    json_path = coverage_json_path or config.REPO_ROOT / "docs" / "coverage.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    comando = [sys.executable, "-m", "coverage", "json", "-o", str(json_path)]
    rc = subprocess.run(comando, check=False, env=env).returncode
    if rc == 0:
        _LOGGER.info("[quality-gate] coverage.json generado en %s", json_path.relative_to(config.REPO_ROOT))
    return rc
