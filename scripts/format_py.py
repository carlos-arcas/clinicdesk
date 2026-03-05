"""Comando canónico para formatear solo archivos Python."""

from __future__ import annotations

import os
import subprocess
import sys

from ._ruff_targets import obtener_targets_python, resolver_repo_root


def main() -> int:
    repo_root = resolver_repo_root()
    os.chdir(repo_root)
    targets = obtener_targets_python(repo_root)
    comando = [sys.executable, "-m", "ruff", "format", *targets]
    return subprocess.run(comando, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
