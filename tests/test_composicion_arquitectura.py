from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

from clinicdesk.app.container import build_container


REPO_ROOT = Path(__file__).resolve().parents[1]


def _crear_db_temporal() -> sqlite3.Connection:
    conexion = sqlite3.connect(":memory:")
    schema_path = REPO_ROOT / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"
    conexion.executescript(schema_path.read_text(encoding="utf-8"))
    conexion.commit()
    return conexion


def test_build_container_con_sqlite_memoria() -> None:
    conexion = _crear_db_temporal()
    try:
        contenedor = build_container(conexion)
    finally:
        conexion.close()
    assert contenedor.pacientes_repo is not None
    assert contenedor.prediccion_ausencias_facade is not None


def _imports_python(path_archivo: Path) -> list[str]:
    modulo = ast.parse(path_archivo.read_text(encoding="utf-8"), filename=path_archivo.as_posix())
    imports: list[str] = []
    for nodo in ast.walk(modulo):
        if isinstance(nodo, ast.Import):
            imports.extend(alias.name for alias in nodo.names)
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            imports.append(nodo.module)
    return imports


def test_application_y_domain_no_dependen_de_ui() -> None:
    rutas = [REPO_ROOT / "clinicdesk" / "app" / "application", REPO_ROOT / "clinicdesk" / "app" / "domain"]
    violaciones: list[str] = []
    for ruta_base in rutas:
        for archivo in ruta_base.rglob("*.py"):
            for modulo in _imports_python(archivo):
                if modulo.startswith("clinicdesk.app.ui") or modulo.startswith("clinicdesk.app.pages"):
                    relativo = archivo.relative_to(REPO_ROOT)
                    violaciones.append(f"{relativo}: {modulo}")
    assert not violaciones, "Dependencias UI detectadas en core:\n" + "\n".join(violaciones)
