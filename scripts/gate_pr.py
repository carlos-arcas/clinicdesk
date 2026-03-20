"""Gate completo canónico del repositorio.

Este comando es la fuente única para CI y PR:
`python -m scripts.gate_pr`.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from scripts.quality_gate_components.doctor_entorno_calidad_core import codigo_salida_estable, diagnosticar_entorno_calidad
from scripts.quality_gate_components.toolchain import COMANDO_DOCTOR

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    returncode_doctor = None
    try:
        diagnostico = diagnosticar_entorno_calidad(REPO_ROOT)
        returncode_doctor = codigo_salida_estable(diagnostico)
    except Exception:  # pragma: no cover - fallback defensivo del wrapper
        logging.exception("[gate-pr] Error inesperado ejecutando doctor de entorno previo al gate.")

    if returncode_doctor and returncode_doctor != 0:
        sys.stderr.write(
            "[gate-pr][entorno] El doctor detectó un bloqueo de tooling; el gate real probablemente fallará antes de validar producto. "
            f"Ejecuta {COMANDO_DOCTOR} para ver el detalle accionable.\n"
        )

    comando = [sys.executable, "scripts/quality_gate.py", "--strict"]
    return subprocess.run(comando, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
