from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORIO = ROOT / "repositorio"


def main() -> int:
    if not REPOSITORIO.exists():
        print("OK: no existe carpeta /repositorio, sin tests legacy.")
        return 0

    encontrados = [p for p in REPOSITORIO.rglob("test_*.py")]
    if encontrados:
        print("ERROR: tests prohibidos dentro de /repositorio:")
        for path in encontrados:
            print(f" - {path.relative_to(ROOT)}")
        return 1

    print("OK: 0 tests en /repositorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
