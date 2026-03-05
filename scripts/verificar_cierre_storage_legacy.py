from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if ROOT.as_posix() not in sys.path:
    sys.path.insert(0, ROOT.as_posix())

from scripts.auditar_storage_legacy_por_proyecto import auditar


def main() -> int:
    resultados = auditar()
    ambos = [fila for fila in resultados if fila["estado"] == "AMBOS"]
    if ambos:
        print("ERROR: aún existen proyectos en estado AMBOS:")
        for fila in ambos:
            print(f" - {fila['proyecto']}")
        return 1
    print("OK: no hay proyectos en estado AMBOS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
