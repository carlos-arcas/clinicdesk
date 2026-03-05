from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTARIO = ROOT / "docs" / "audit" / "legacy_repo_inventory_final.md"


def recolectar_carpetas_legacy_importantes(repo_root: Path) -> list[Path]:
    candidatos = [
        repo_root / "repositorio" / "src" / "legacy",
        repo_root / "legacy",
        repo_root / "corcho_legacy",
    ]
    carpetas: list[Path] = []
    for base in candidatos:
        if not base.exists():
            continue
        for ruta in sorted(base.rglob("*")):
            if ruta.is_dir() and _es_carpeta_legacy(ruta.name):
                carpetas.append(ruta.relative_to(repo_root))
    return sorted(set(carpetas))


def _es_carpeta_legacy(nombre: str) -> bool:
    texto = nombre.lower()
    return "legacy" in texto or "graveyard" in texto or "archivado" in texto


def rutas_documentadas(inventario_path: Path) -> set[str]:
    patron = re.compile(r"^\|\s*`([^`]+)`\s*\|")
    encontradas: set[str] = set()
    for linea in inventario_path.read_text(encoding="utf-8").splitlines():
        match = patron.match(linea.strip())
        if match:
            encontradas.add(match.group(1).strip("/"))
    return encontradas


def verificar(repo_root: Path = ROOT) -> tuple[list[str], list[str]]:
    inventario = repo_root / "docs" / "audit" / "legacy_repo_inventory_final.md"
    if not inventario.exists():
        return [], [f"Falta inventario requerido: {inventario.relative_to(repo_root)}"]

    documentadas = rutas_documentadas(inventario)
    detectadas = [str(path).strip("/") for path in recolectar_carpetas_legacy_importantes(repo_root)]
    faltantes = [ruta for ruta in detectadas if ruta not in documentadas]
    return detectadas, faltantes


def main() -> int:
    detectadas, faltantes = verificar()
    print(f"Carpetas legacy detectadas: {len(detectadas)}")
    for ruta in detectadas:
        print(f" - {ruta}")

    if faltantes:
        print("ERROR: carpetas legacy sin inventariar:")
        for ruta in faltantes:
            print(f" - {ruta}")
        return 1

    if not INVENTARIO.exists():
        print(f"ERROR: falta inventario requerido: {INVENTARIO.relative_to(ROOT)}")
        return 1

    print("OK: inventario legacy presente y trazable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
