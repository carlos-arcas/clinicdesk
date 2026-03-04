from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class ErrorLockDeps(RuntimeError):
    """Error de lock de dependencias."""


def _pip_compile_disponible() -> str:
    ejecutable = shutil.which("pip-compile")
    if ejecutable:
        return ejecutable

    comando = [sys.executable, "-m", "piptools", "--version"]
    resultado = subprocess.run(comando, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if resultado.returncode == 0:
        return f"{sys.executable} -m piptools compile"

    raise ErrorLockDeps(
        "No se encontró pip-tools. Instala dependencias dev con: python -m pip install -r requirements-dev.txt"
    )


def _run(comando: list[str], descripcion: str) -> None:
    resultado = subprocess.run(comando, cwd=REPO_ROOT, check=False)
    if resultado.returncode != 0:
        raise ErrorLockDeps(f"Falló '{descripcion}' con exit code {resultado.returncode}.")


def _comando_compile(base: list[str], entrada: str, salida: str) -> list[str]:
    return [*base, "--output-file", salida, entrada]


def main() -> int:
    try:
        ejecutable = _pip_compile_disponible()
        if ejecutable.endswith("pip-compile"):
            base = [ejecutable]
        else:
            base = [sys.executable, "-m", "piptools", "compile"]

        _run(_comando_compile(base, "requirements.in", "requirements.txt"), "lock runtime")
        _run(_comando_compile(base, "requirements-dev.in", "requirements-dev.txt"), "lock dev")
    except ErrorLockDeps as exc:
        sys.stdout.write(f"[lock-deps][error] {exc}\n")
        return 1

    sys.stdout.write("[lock-deps] Locks regenerados: requirements.txt y requirements-dev.txt\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
