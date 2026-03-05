from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PROYECTOS = ROOT / "data" / "proyectos"
LEGACY_DIR = "storage_legacy"
NUEVO_DIR = "storage"


def estado_proyecto(path: Path) -> str:
    legacy = (path / LEGACY_DIR).exists()
    nuevo = (path / NUEVO_DIR).exists()
    if legacy and nuevo:
        return "AMBOS"
    if legacy:
        return "SOLO_LEGACY"
    if nuevo:
        return "SOLO_NUEVO"
    return "NINGUNO"


def auditar() -> list[dict[str, str]]:
    if not BASE_PROYECTOS.exists():
        return []
    resultados: list[dict[str, str]] = []
    for proyecto in sorted([p for p in BASE_PROYECTOS.iterdir() if p.is_dir()]):
        resultados.append({"proyecto": proyecto.name, "estado": estado_proyecto(proyecto)})
    return resultados


def main() -> int:
    resultados = auditar()
    resumen = {"SOLO_LEGACY": 0, "SOLO_NUEVO": 0, "AMBOS": 0, "NINGUNO": 0}
    for fila in resultados:
        resumen[fila["estado"]] += 1

    print(json.dumps({"proyectos": resultados, "resumen": resumen}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
