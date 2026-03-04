from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / ".venv"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _run_command(command: list[str], descripcion: str) -> None:
    _log(f"[setup] {descripcion}: {' '.join(command)}")
    resultado = subprocess.run(command, cwd=PROJECT_ROOT)
    if resultado.returncode != 0:
        raise RuntimeError(f"Fallo '{descripcion}' (exit code {resultado.returncode}).")


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

    _run_command([str(python_venv), "-m", "pip", "install", "-r", "requirements.txt"], "Instalar dependencias runtime")
    _run_command(
        [str(python_venv), "-m", "pip", "install", "-r", "requirements-dev.txt"],
        "Instalar dependencias dev",
    )


def _verificar_herramientas(python_venv: Path) -> None:
    verificaciones = [
        ("ruff", [str(python_venv), "-m", "ruff", "--version"]),
        ("pytest", [str(python_venv), "-m", "pytest", "--version"]),
        ("pip-audit", [str(python_venv), "-m", "pip_audit", "--version"]),
        ("mypy", [str(python_venv), "-m", "mypy", "--version"]),
    ]
    for nombre, comando in verificaciones:
        _run_command(comando, f"Verificar herramienta {nombre}")


def _log(mensaje: str) -> None:
    sys.stdout.write(f"{mensaje}\n")


def main() -> int:
    try:
        _crear_venv_si_no_existe()
        python_venv = _venv_python()
        if not python_venv.exists():
            raise RuntimeError(f"No se encontró el Python del venv: {python_venv}")
        _advertir_requirements_no_pinneados()
        _instalar_dependencias(python_venv)
        _verificar_herramientas(python_venv)
    except RuntimeError as exc:
        _log(f"[setup][error] {exc}")
        return 1

    _log("[setup] Entorno listo. Puedes ejecutar la app con: python scripts/run_app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
