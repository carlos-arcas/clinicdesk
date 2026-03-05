"""Comando canónico para lint de archivos Python con Ruff."""

from __future__ import annotations

import os
import subprocess
import sys

from ._ruff_targets import obtener_targets_python, resolver_repo_root


def main() -> int:
    repo_root = resolver_repo_root()
    os.chdir(repo_root)
    targets = obtener_targets_python(repo_root)
    comandos = (
        [sys.executable, "-m", "ruff", "check", *targets],
        [sys.executable, "-m", "ruff", "format", "--check", *targets],
    )
    for comando in comandos:
        resultado = subprocess.run(comando, check=False)
        if resultado.returncode != 0:
            return resultado.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
