from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if ROOT.as_posix() not in sys.path:
    sys.path.insert(0, ROOT.as_posix())

from scripts.auditar_storage_legacy_por_proyecto import auditar


def main() -> int:
    resultados = auditar()
    print(f"Proyectos auditados: {len(resultados)}")
    for fila in resultados:
        print(f" - {fila['proyecto']}: {fila['estado']}")
    print("OK: verificación de storage por proyecto completada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
