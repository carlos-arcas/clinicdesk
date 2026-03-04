"""Verifica que existan los documentos mínimos de seguridad del repositorio."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_SECURITY_DOCS = (
    Path("docs/threat_model.md"),
    Path("docs/security_regression_checklist.md"),
)


def find_missing_security_docs(repo_root: Path) -> list[Path]:
    missing: list[Path] = []
    for rel_path in REQUIRED_SECURITY_DOCS:
        if not (repo_root / rel_path).exists():
            missing.append(rel_path)
    return missing


def check_security_docs(repo_root: Path) -> int:
    missing = find_missing_security_docs(repo_root=repo_root)
    if not missing:
        return 0

    docs = ", ".join(str(path) for path in missing)
    sys.stderr.write(
        "[quality-gate] ❌ Faltan documentos de seguridad requeridos: "
        f"{docs}. "
        "Crea estos archivos antes de ejecutar python -m scripts.gate_pr.\n"
    )
    return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Comprueba presencia de docs de seguridad obligatorios.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Raíz del repositorio que contiene la carpeta docs/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return check_security_docs(repo_root=args.repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
