"""Wrapper oficial para ejecutar el gate en entornos sandbox."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGGER = logging.getLogger(__name__)


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("CLINICDESK_SANDBOX_MODE", "1")
    return env


def main() -> int:
    os.chdir(REPO_ROOT)
    comando = [sys.executable, "-m", "scripts.gate_pr"]
    try:
        return subprocess.run(comando, check=False, env=_build_env()).returncode
    except OSError as exc:
        LOGGER.error("Error ejecutando gate sandbox: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
