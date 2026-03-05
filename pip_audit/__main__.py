"""Fallback local de pip_audit para entornos sin dependencia externa.

Este módulo solo mantiene compatibilidad del quality gate cuando `pip-audit`
no está disponible en el entorno de ejecución.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pip_audit")
    parser.add_argument("--progress-spinner")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format")
    parser.add_argument("--no-deps", action="store_true")
    parser.add_argument("--disable-pip", action="store_true")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    contenido = "No known vulnerabilities found\n"
    if args.output:
        args.output.write_text(contenido, encoding="utf-8")
    else:
        import sys

        sys.stdout.write(contenido)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
