# bootstrap.py
"""
Bootstrap de la aplicación ClinicDesk.

Responsabilidades:
- Resolver rutas del proyecto
- Inicializar SQLite
- Aplicar schema.sql
- Devolver la conexión lista para usar

Este archivo es infraestructura pura.
No contiene lógica de dominio ni de aplicación.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


# ---------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------


def project_root() -> Path:
    """Devuelve la raíz del proyecto."""
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    """Directorio donde se guarda la base de datos."""
    return project_root() / "data"


def db_path() -> Path:
    """Ruta al archivo SQLite."""
    return data_dir() / "clinicdesk.sqlite"


def schema_path() -> Path:
    """Ruta al archivo schema.sql."""
    return project_root() / "infrastructure" / "sqlite" / "schema.sql"


# ---------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------


def _apply_pragmas(con: sqlite3.Connection) -> None:
    """
    PRAGMAs recomendados para SQLite en apps de escritorio.
    """
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")
    con.execute("PRAGMA temp_store = MEMORY;")
    con.execute("PRAGMA busy_timeout = 5000;")


def _apply_schema(con: sqlite3.Connection) -> None:
    """
    Aplica el schema SQL (idempotente).
    """
    path = schema_path()
    if not path.exists():
        raise FileNotFoundError(f"No se encuentra schema.sql en {path}")

    sql = path.read_text(encoding="utf-8")
    con.executescript(sql)
    _migrate_stock_columns(con)
    con.commit()


def _migrate_stock_columns(con: sqlite3.Connection) -> None:
    """
    Migra columnas legacy de stock si existen en la base de datos.
    """
    _ensure_stock_column(con, table="medicamentos")
    _ensure_stock_column(con, table="materiales")


def _ensure_stock_column(con: sqlite3.Connection, *, table: str) -> None:
    columns = {
        row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if "cantidad_en_almacen" in columns:
        return
    if "cantidad_almacen" not in columns:
        return

    con.execute(
        f"ALTER TABLE {table} ADD COLUMN cantidad_en_almacen INTEGER NOT NULL DEFAULT 0"
    )
    con.execute(
        f"UPDATE {table} SET cantidad_en_almacen = cantidad_almacen"
    )


# ---------------------------------------------------------------------
# Bootstrap principal
# ---------------------------------------------------------------------


def bootstrap_database(apply_schema: bool = True) -> sqlite3.Connection:
    """
    Inicializa la base de datos de la aplicación.

    Flujo:
    - Crea carpeta /data si no existe
    - Abre conexión SQLite
    - Aplica PRAGMAs
    - Aplica schema.sql
    - Devuelve la conexión
    """
    data_dir().mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db_path().as_posix())
    con.row_factory = sqlite3.Row

    _apply_pragmas(con)

    if apply_schema:
        _apply_schema(con)

    return con
