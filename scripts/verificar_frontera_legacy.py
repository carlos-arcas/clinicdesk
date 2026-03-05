from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def main() -> int:
    if not SRC.exists():
        print("OK: no existe /src en este repositorio; frontera legacy sin incidencias.")
        return 0

    violaciones: list[str] = []
    for py in SRC.rglob("*.py"):
        texto = py.read_text(encoding="utf-8")
        if "repositorio" in texto and "import" in texto:
            violaciones.append(str(py.relative_to(ROOT)))
    if violaciones:
        print("ERROR: imports legacy detectados:")
        for item in violaciones:
            print(f" - {item}")
        return 1
    print("OK: sin imports legacy en /src.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
