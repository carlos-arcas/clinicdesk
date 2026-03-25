from __future__ import annotations

import sys

from .doctor_entorno_calidad_core import clasificar_bloqueo_entorno, renderizar_reporte
from .ejecucion_canonica import EXIT_ENTORNO_BLOQUEADO
from .toolchain import COMANDO_SETUP


def reportar_bloqueo_operativo_doctor(
    *,
    etiqueta_gate: str,
    returncode_doctor: int,
    diagnostico,
    comando_reintento: str,
    validaciones_no_ejecutadas: str | None = None,
) -> int:
    sys.stderr.write(
        f"[{etiqueta_gate}][entorno] Gate abortado por bloqueo del toolchain local; todavía no se validó el proyecto.\n"
    )
    sys.stderr.write(
        f"[{etiqueta_gate}][entorno] rc={EXIT_ENTORNO_BLOQUEADO} significa bloqueo operativo local (doctor rc={returncode_doctor}), no fallo funcional del repositorio.\n"
    )
    clasificacion = clasificar_bloqueo_entorno(diagnostico)
    if clasificacion is not None:
        sys.stderr.write(
            f"[{etiqueta_gate}][diagnostico] reason_code={clasificacion.reason_code}; categoria={clasificacion.categoria}\n"
        )
        sys.stderr.write(f"[{etiqueta_gate}][diagnostico] detalle={clasificacion.detalle}\n")
        sys.stderr.write(f"[{etiqueta_gate}][accion] Paso sugerido: {clasificacion.accion_sugerida}\n")
    if validaciones_no_ejecutadas is not None:
        sys.stderr.write(
            f"[{etiqueta_gate}][entorno] Validaciones no ejecutadas: {validaciones_no_ejecutadas}.\n"
        )
    for linea in renderizar_reporte(diagnostico):
        sys.stderr.write(f"{linea}\n")
    sys.stderr.write(
        f"[{etiqueta_gate}][accion] Corrige el entorno con la guía anterior y reintenta: {comando_reintento}\n"
    )
    if hasattr(diagnostico, "interprete") and not diagnostico.interprete.usa_python_repo:
        sys.stderr.write(
            f"[{etiqueta_gate}][accion] Si el venv del repo no está activo o quedó corrupto, recréalo con: {COMANDO_SETUP}\n"
        )
    return EXIT_ENTORNO_BLOQUEADO
