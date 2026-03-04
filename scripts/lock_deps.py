from __future__ import annotations

import subprocess
import sys


MENSAJE_ERROR_PIP_TOOLS = (
    "pip-tools no está instalado. Ejecuta: python -m pip install pip-tools "
    "o instala dependencias de desarrollo con requirements-dev.txt"
)


def _ejecutar_pip_compile(archivo_entrada: str, archivo_salida: str) -> int:
    comando = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--resolver",
        "backtracking",
        "--output-file",
        archivo_salida,
        archivo_entrada,
    ]
    resultado = subprocess.run(comando, check=False)
    return resultado.returncode


def main() -> int:
    try:
        __import__("piptools")
    except ModuleNotFoundError:
        sys.stderr.write(f"{MENSAJE_ERROR_PIP_TOOLS}\n")
        return 1

    runtime_rc = _ejecutar_pip_compile("requirements.in", "requirements.txt")
    if runtime_rc != 0:
        return runtime_rc

    return _ejecutar_pip_compile("requirements-dev.in", "requirements-dev.txt")


if __name__ == "__main__":
    raise SystemExit(main())
