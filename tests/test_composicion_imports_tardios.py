from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUTA_COMPOSICION = REPO_ROOT / "clinicdesk" / "app" / "composicion"
ALLOWLIST_IMPORTS_TARDIOS: dict[str, str] = {}


def _es_import_tardio(nodo: ast.AST) -> bool:
    return isinstance(nodo, (ast.Import, ast.ImportFrom))


def _imports_tardios(path_archivo: Path) -> list[int]:
    modulo = ast.parse(path_archivo.read_text(encoding="utf-8"), filename=path_archivo.as_posix())
    lineas: list[int] = []
    for nodo in ast.walk(modulo):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for hijo in ast.walk(nodo):
                if _es_import_tardio(hijo):
                    lineas.append(hijo.lineno)
    return sorted(set(lineas))


def test_composicion_no_tiene_imports_tardios_fuera_allowlist() -> None:
    violaciones: list[str] = []
    for archivo in sorted(RUTA_COMPOSICION.glob("*.py")):
        relativo = archivo.relative_to(REPO_ROOT).as_posix()
        if relativo in ALLOWLIST_IMPORTS_TARDIOS:
            continue
        lineas = _imports_tardios(archivo)
        if lineas:
            violaciones.append(f"{relativo}: imports tardíos en líneas {lineas}")

    assert not violaciones, (
        "Se detectaron imports tardíos en composiciones fuera de la allowlist:\n"
        + "\n".join(violaciones)
    )
