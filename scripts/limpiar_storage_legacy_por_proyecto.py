from __future__ import annotations

import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if ROOT.as_posix() not in sys.path:
    sys.path.insert(0, ROOT.as_posix())

from scripts.auditar_storage_legacy_por_proyecto import BASE_PROYECTOS, LEGACY_DIR, auditar

BACKUP_BASE = ROOT / "data" / "backups" / "storage_legacy_quarantine"


def limpiar(apply: bool) -> int:
    resultados = auditar()
    objetivos = [fila["proyecto"] for fila in resultados if fila["estado"] == "AMBOS"]

    if not objetivos:
        print("No hay proyectos en estado AMBOS. Sin cambios.")
        return 0

    print(f"Proyectos AMBOS detectados: {len(objetivos)}")
    for proyecto in objetivos:
        legacy_path = BASE_PROYECTOS / proyecto / LEGACY_DIR
        destino = BACKUP_BASE / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") / proyecto / LEGACY_DIR
        print(f" - {proyecto}: {legacy_path} -> {destino}")
        if apply:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(legacy_path.as_posix(), destino.as_posix())

    print("Modo APPLY ejecutado." if apply else "Modo DRY-RUN: sin cambios.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply = args.apply and not args.dry_run
    return limpiar(apply=apply)


if __name__ == "__main__":
    raise SystemExit(main())
