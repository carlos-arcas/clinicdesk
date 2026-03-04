"""Validador básico de CHANGELOG en formato Keep a Changelog."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from clinicdesk import __version__

_SECCIONES_VALIDAS = ("Added", "Changed", "Fixed", "Security")


def _bloque_version(contenido: str, version: str) -> str:
    patron = re.compile(
        rf"^##\s+\[{re.escape(version)}\].*?$\n(?P<bloque>.*?)(?=^##\s+\[|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    coincidencia = patron.search(contenido)
    if coincidencia is None:
        raise ValueError(f"No existe sección para la versión actual [{version}] en CHANGELOG.md.")
    return coincidencia.group("bloque")


def _tiene_bullet_en_secciones(bloque: str) -> bool:
    for seccion in _SECCIONES_VALIDAS:
        patron_seccion = re.compile(
            rf"^###\s+{seccion}\s*$\n(?P<contenido>.*?)(?=^###\s+|\Z)",
            flags=re.MULTILINE | re.DOTALL,
        )
        coincidencia = patron_seccion.search(bloque)
        if coincidencia is None:
            continue
        if re.search(r"^\s*[-*]\s+\S+", coincidencia.group("contenido"), flags=re.MULTILINE):
            return True
    return False


def check_changelog(path: Path, version: str) -> None:
    contenido = path.read_text(encoding="utf-8")
    bloque = _bloque_version(contenido, version)
    if not _tiene_bullet_en_secciones(bloque):
        raise ValueError(
            "La sección de la versión actual debe incluir al menos un bullet "
            "en Added/Changed/Fixed/Security."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida CHANGELOG.md")
    parser.add_argument("--check", action="store_true", help="Ejecuta validación de CHANGELOG.")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Ruta del changelog a validar.",
    )
    parser.add_argument(
        "--version",
        default=__version__,
        help="Versión esperada. Por defecto usa clinicdesk.__version__.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.check:
        return 0
    check_changelog(path=args.path, version=args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
