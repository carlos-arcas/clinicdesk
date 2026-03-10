from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.quality_gate_components.doctor_entorno_calidad_core import (
    codigo_salida_estable,
    diagnosticar_entorno_calidad,
    renderizar_reporte,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Doctor/preflight de entorno de calidad.")
    parser.add_argument("--require-wheelhouse", action="store_true", help="Falla si wheelhouse no está disponible.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    diagnostico = diagnosticar_entorno_calidad(REPO_ROOT)
    for linea in renderizar_reporte(diagnostico, exigir_wheelhouse=args.require_wheelhouse):
        sys.stdout.write(f"{linea}\n")
    return codigo_salida_estable(diagnostico, exigir_wheelhouse=args.require_wheelhouse)


if __name__ == "__main__":
    raise SystemExit(main())
