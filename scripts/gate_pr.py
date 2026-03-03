"""Gate completo canónico del repositorio.

Este comando es la fuente única para CI y PR:
`python -m scripts.gate_pr`.
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    comando = [sys.executable, "scripts/quality_gate.py", "--strict"]
    return subprocess.run(comando, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
