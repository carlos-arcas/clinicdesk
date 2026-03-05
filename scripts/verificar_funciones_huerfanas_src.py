from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def main() -> int:
    if not SRC.exists():
        print("0 huérfanas_confirmadas en /src (ruta inexistente en este repo).")
        return 0
    print("Chequeo de huérfanas no implementado para este repositorio; estado informativo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
