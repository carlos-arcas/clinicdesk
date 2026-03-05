from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_DOCS = [
    ROOT / "docs" / "operacion" / "cierre_storage_legacy.md",
    ROOT / "docs" / "audit" / "legacy_repo_inventory_final.md",
]


def main() -> int:
    faltantes = [p for p in REQUIRED_DOCS if not p.exists()]
    if faltantes:
        print("ERROR: faltan documentos de cierre legacy:")
        for ruta in faltantes:
            print(f" - {ruta.relative_to(ROOT)}")
        return 1
    print("OK: reglas mínimas documentales en verde.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
