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
    REASON_CODES_OPERATIVOS_DOCTOR,
    clasificar_bloqueo_entorno,
    codigo_salida_estable,
    diagnosticar_entorno_calidad,
    renderizar_reporte,
)
from scripts.quality_gate_components.contrato_reason_codes_doc import cargar_reason_codes_documentados
from scripts.quality_gate_components.ejecucion_canonica import (
    REASON_CODES_OPERATIVOS_CANONICO,
    reejecutar_en_python_objetivo,
    renderizar_bloqueo,
    resolver_ejecucion_canonica,
)
from scripts.quality_gate_components.toolchain import COMANDO_DOCTOR, COMANDO_SETUP

REPO_ROOT = Path(__file__).resolve().parents[1]
EXIT_ENTORNO_BLOQUEADO = 20
VALIDACIONES_NO_EJECUTADAS = "lint, typecheck, pytest, cobertura, golden, i18n, seguridad"


def reason_codes_operativos_documentables() -> tuple[str, ...]:
    return tuple(sorted({*REASON_CODES_OPERATIVOS_CANONICO, *REASON_CODES_OPERATIVOS_DOCTOR}))


def reason_codes_operativos_documentados_en_docs(ruta_doc: Path) -> tuple[str, ...]:
    return cargar_reason_codes_documentados(ruta_doc)


def _preflight_entorno(repo_root: Path) -> int:
    try:
        diagnostico = diagnosticar_entorno_calidad(repo_root)
    except Exception:  # pragma: no cover
        logging.exception("[gate-pr] Error inesperado ejecutando doctor de entorno previo al gate.")
        return 0

    returncode_doctor = codigo_salida_estable(diagnostico)
    if returncode_doctor == 0:
        return 0

    clasificacion = clasificar_bloqueo_entorno(diagnostico)
    sys.stderr.write(
        "[gate-pr][entorno] Gate abortado por bloqueo del toolchain local; todavía no se validó el proyecto.\n"
    )
    sys.stderr.write(
        f"[gate-pr][entorno] rc={EXIT_ENTORNO_BLOQUEADO} significa bloqueo operativo local (doctor rc={returncode_doctor}), no fallo funcional del repositorio.\n"
    )
    if clasificacion is not None:
        sys.stderr.write(
            f"[gate-pr][diagnostico] reason_code={clasificacion.reason_code}; categoria={clasificacion.categoria}\n"
        )
        sys.stderr.write(f"[gate-pr][diagnostico] detalle={clasificacion.detalle}\n")
        sys.stderr.write(f"[gate-pr][accion] Paso sugerido: {clasificacion.accion_sugerida}\n")
    sys.stderr.write(
        f"[gate-pr][entorno] Validaciones no ejecutadas: {VALIDACIONES_NO_EJECUTADAS}.\n"
    )
    for linea in renderizar_reporte(diagnostico):
        sys.stderr.write(f"{linea}\n")
    sys.stderr.write(
        f"[gate-pr][accion] Corrige el entorno con la guía anterior y reintenta: {COMANDO_DOCTOR}\n"
    )
    if hasattr(diagnostico, "interprete") and not diagnostico.interprete.usa_python_repo:
        sys.stderr.write(
            f"[gate-pr][accion] Si el venv del repo no está activo o quedó corrupto, recréalo con: {COMANDO_SETUP}\n"
        )
    return EXIT_ENTORNO_BLOQUEADO


def main() -> int:
    decision = resolver_ejecucion_canonica(REPO_ROOT, exigir_venv_repo=True)
    if decision.accion == "reejecutar":
        return reejecutar_en_python_objetivo(decision, ["-m", "scripts.gate_pr", *sys.argv[1:]])
    if decision.accion == "bloquear":
        for linea in renderizar_bloqueo(decision):
            sys.stderr.write(f"{linea}\n")
        return EXIT_ENTORNO_BLOQUEADO

    preflight = _preflight_entorno(REPO_ROOT)
    if preflight != 0:
        return preflight

    comando = [sys.executable, "scripts/quality_gate.py", "--strict"]
    return subprocess.run(comando, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
