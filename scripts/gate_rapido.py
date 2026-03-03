"""Gate rápido canónico del repositorio.

Este comando conserva un contrato estable (`python -m scripts.gate_rapido`)
y delega la ejecución al gate actual en modo rápido/report-only.
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    comando = [sys.executable, "scripts/quality_gate.py", "--report-only"]
    return subprocess.run(comando, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
