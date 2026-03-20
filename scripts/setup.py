from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from scripts.quality_gate_components.bootstrap_dependencias import comando_instalacion, resolver_wheelhouse
from scripts.quality_gate_components.doctor_entorno_calidad_core import (
    codigo_salida_estable,
    diagnosticar_entorno_calidad,
    renderizar_reporte,
)
from scripts.quality_gate_components.toolchain import COMANDO_DOCTOR, COMANDO_GATE


def resolve_repo_root() -> Path:
    override = os.environ.get("CLINICDESK_REPO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


PROJECT_ROOT = resolve_repo_root()
VENV_DIR = PROJECT_ROOT / ".venv"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _log(mensaje: str) -> None:
    sys.stdout.write(f"{mensaje}\n")


def _resumen_error_instalacion(stderr: str, stdout: str) -> list[str]:
    texto = f"{stdout}\n{stderr}".lower()
    if any(token in texto for token in ("proxyerror", "proxy", "407 proxy", "tunnel connection failed")):
        return [
            "[setup][diagnostico] Fallo de red/proxy detectado durante instalación.",
            "[setup][accion] Revisa HTTP_PROXY/HTTPS_PROXY o usa un índice accesible antes de reintentar.",
        ]
    if any(token in texto for token in ("temporary failure in name resolution", "failed to establish a new connection", "connection timed out")):
        return [
            "[setup][diagnostico] Fallo de conectividad a índices Python detectado.",
            "[setup][accion] Sin wheelhouse ni acceso a red, este entorno no es recuperable localmente.",
        ]
    if "no matching distribution found" in texto or "could not find a version that satisfies the requirement" in texto:
        return [
            "[setup][diagnostico] El lock pide una versión que pip no pudo resolver con el índice actual.",
            "[setup][accion] Verifica índice/proxy y que el lock esté actualizado antes de reintentar.",
        ]
    return []


def _run_command(command: list[str], descripcion: str) -> None:
    _log(f"[setup] {descripcion}: {' '.join(command)}")
    resultado = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    if resultado.stdout:
        _log(resultado.stdout.rstrip())
    if resultado.stderr:
        _log(resultado.stderr.rstrip())
    if resultado.returncode != 0:
        pistas = _resumen_error_instalacion(resultado.stderr or "", resultado.stdout or "")
        detalle = f"Fallo '{descripcion}' (exit code {resultado.returncode})."
        if pistas:
            detalle = f"{detalle} {' '.join(linea.replace('[setup][diagnostico] ', '').replace('[setup][accion] ', '') for linea in pistas)}"
        raise RuntimeError(detalle)


def _crear_venv_si_no_existe() -> None:
    if VENV_DIR.exists():
        _log(f"[setup] Entorno virtual ya existe en {VENV_DIR}")
        return
    _run_command([sys.executable, "-m", "venv", str(VENV_DIR)], "Crear entorno virtual .venv")


def _requirements_con_rango(requirements_path: Path) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for numero_linea, linea in enumerate(requirements_path.read_text(encoding="utf-8").splitlines(), start=1):
        contenido = linea.strip()
        if not contenido or contenido.startswith("#") or contenido.startswith(("-", "--")):
            continue
        if "==" not in contenido:
            offenders.append((numero_linea, contenido))
    return offenders


def _advertir_requirements_no_pinneados() -> None:
    for nombre in ("requirements.txt", "requirements-dev.txt"):
        ruta = PROJECT_ROOT / nombre
        if not ruta.exists():
            continue
        offenders = _requirements_con_rango(ruta)
        if not offenders:
            continue
        _log(f"[setup][warn] {nombre} contiene entradas sin pin estricto (==):")
        for numero_linea, contenido in offenders:
            _log(f"[setup][warn]   - linea {numero_linea}: {contenido}")


def _instalar_dependencias(python_venv: Path) -> None:
    requirements = PROJECT_ROOT / "requirements.txt"
    requirements_dev = PROJECT_ROOT / "requirements-dev.txt"
    if not requirements.exists() or not requirements_dev.exists():
        raise RuntimeError("No se encontraron requirements.txt y/o requirements-dev.txt en la raíz del repositorio.")

    wheelhouse = resolver_wheelhouse(PROJECT_ROOT)
    comando_runtime, modo_runtime = comando_instalacion(str(python_venv), requirements, wheelhouse)
    comando_dev, modo_dev = comando_instalacion(str(python_venv), requirements_dev, wheelhouse)
    _run_command(comando_runtime, f"Instalar dependencias runtime ({modo_runtime})")
    _run_command(comando_dev, f"Instalar dependencias dev ({modo_dev})")


def _verificar_herramientas(python_venv: Path) -> None:
    verificaciones = [
        ("ruff", [str(python_venv), "-m", "ruff", "--version"]),
        ("pytest", [str(python_venv), "-m", "pytest", "--version"]),
        ("pip-audit", [str(python_venv), "-m", "pip_audit", "--version"]),
        ("mypy", [str(python_venv), "-m", "mypy", "--version"]),
    ]
    for nombre, comando in verificaciones:
        _run_command(comando, f"Verificar herramienta {nombre}")


def main() -> int:
    try:
        diagnostico = diagnosticar_entorno_calidad(PROJECT_ROOT)
        for linea in renderizar_reporte(diagnostico):
            _log(linea)
        _crear_venv_si_no_existe()
        python_venv = _venv_python()
        if not python_venv.exists():
            raise RuntimeError(f"No se encontró el Python del venv: {python_venv}")
        _advertir_requirements_no_pinneados()
        _instalar_dependencias(python_venv)
        _verificar_herramientas(python_venv)
        diagnostico_final = diagnosticar_entorno_calidad(PROJECT_ROOT)
        if codigo_salida_estable(diagnostico_final) != 0:
            raise RuntimeError(
                "El entorno quedó desalineado tras setup. "
                f"Ejecuta {COMANDO_DOCTOR} para el detalle y no lances {COMANDO_GATE} hasta corregirlo."
            )
    except RuntimeError as exc:
        _log(f"[setup][error] {exc}")
        return 1

    _log(f"[setup] Entorno listo. Próximos pasos: {COMANDO_DOCTOR} && {COMANDO_GATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
