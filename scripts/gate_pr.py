"""Gate completo canónico del repositorio.

Este comando es la fuente única para CI y PR:
`python -m scripts.gate_pr`.
"""

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
import sys

from scripts.quality_gate_components.doctor_entorno_calidad_core import (
    codigo_salida_estable,
    diagnosticar_entorno_calidad,
    renderizar_reporte,
)
from scripts.quality_gate_components.toolchain import COMANDO_DOCTOR, COMANDO_SETUP

REPO_ROOT = Path(__file__).resolve().parents[1]
EXIT_ENTORNO_BLOQUEADO = 20


def _preflight_entorno(repo_root: Path) -> int:
    try:
        diagnostico = diagnosticar_entorno_calidad(repo_root)
    except Exception:  # pragma: no cover
        logging.exception("[gate-pr] Error inesperado ejecutando doctor de entorno previo al gate.")
        return 0

    returncode_doctor = codigo_salida_estable(diagnostico)
    if returncode_doctor == 0:
        return 0

    sys.stderr.write(
        "[gate-pr][entorno] Gate abortado por bloqueo del toolchain local; todavía no se validó el proyecto.\n"
    )
    sys.stderr.write(
        f"[gate-pr][entorno] rc={EXIT_ENTORNO_BLOQUEADO} significa bloqueo operativo local (doctor rc={returncode_doctor}), no fallo funcional del repositorio.\n"
    )
    for linea in renderizar_reporte(diagnostico):
        sys.stderr.write(f"{linea}\n")
    sys.stderr.write(
        f"[gate-pr][accion] Corrige el entorno con la guía anterior y reintenta: {COMANDO_DOCTOR}\n"
    )
    if hasattr(diagnostico, 'interprete') and not diagnostico.interprete.usa_python_repo:
        sys.stderr.write(
            f"[gate-pr][accion] Si el venv del repo no está activo o quedó corrupto, recréalo con: {COMANDO_SETUP}\n"
        )
    return EXIT_ENTORNO_BLOQUEADO


def main() -> int:
    preflight = _preflight_entorno(REPO_ROOT)
    if preflight != 0:
        return preflight

    comando = [sys.executable, "scripts/quality_gate.py", "--strict"]
    return subprocess.run(comando, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
