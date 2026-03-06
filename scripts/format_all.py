"""Comando canónico para formateo de repositorio sin incluir Markdown/YAML."""

from __future__ import annotations

import logging
import os
import subprocess
import sys

from ._ruff_targets import resolver_repo_root

LOGGER = logging.getLogger(__name__)


def main() -> int:
    repo_root = resolver_repo_root()
    os.chdir(repo_root)
    comando = [sys.executable, "-m", "scripts.format_py"]
    resultado = subprocess.run(comando, check=False)
    LOGGER.info("format_py ejecutado; markdown/yaml no se formatean aquí")
    return resultado.returncode


if __name__ == "__main__":
    raise SystemExit(main())
