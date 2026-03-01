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
from os import getenv
from pathlib import Path

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.common.field_crypto_flags import validate_field_crypto_configuration
from clinicdesk.app.infrastructure.sqlite.sqlite_datetime_codecs import (
    register_sqlite_datetime_codecs,
)
from clinicdesk.app.infrastructure.sqlite.field_crypto_migrations import (
    ensure_medicos_field_crypto_columns,
    ensure_pacientes_field_crypto_columns,
)
from clinicdesk.app.infrastructure.sqlite.pii_crypto import (
    configure_connection_pii,
    migrate_existing_pii_data,
)


LOGGER = get_logger(__name__)

def _is_special_sqlite_path(raw_path: str) -> bool:
    return raw_path == ":memory:" or raw_path.startswith("file:")


# ---------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------


def project_root() -> Path:
    """Devuelve la raíz del proyecto."""
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    """Directorio donde se guarda la base de datos."""
    return Path("./data")


def resolve_db_path(sqlite_path_arg: str | None = None, *, emit_log: bool = True) -> Path:
    """Resuelve la ruta SQLite desde arg/env/default con trazabilidad en logs."""
    if sqlite_path_arg:
        resolved = Path(sqlite_path_arg) if _is_special_sqlite_path(sqlite_path_arg) else Path(sqlite_path_arg).expanduser().resolve()
        source = "arg"
    else:
        configured = getenv("CLINICDESK_DB_PATH")
        if configured:
            resolved = Path(configured) if _is_special_sqlite_path(configured) else Path(configured).expanduser().resolve()
            source = "env"
        else:
            resolved = (data_dir() / "clinicdesk.db").expanduser().resolve()
            source = "default"
    if emit_log:
        LOGGER.info("db_path_resolved path=%s source=%s", resolved, source)
    return resolved


def db_path() -> Path:
    """Ruta al archivo SQLite (compatibilidad)."""
    return resolve_db_path(emit_log=False)


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
    ensure_pacientes_field_crypto_columns(con)
    ensure_medicos_field_crypto_columns(con)
    migrate_existing_pii_data(con)
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


def bootstrap_database(apply_schema: bool = True, sqlite_path: str | None = None) -> sqlite3.Connection:
    """
    Inicializa la base de datos de la aplicación.

    Flujo:
    - Crea carpeta /data si no existe
    - Abre conexión SQLite
    - Aplica PRAGMAs
    - Aplica schema.sql
    - Devuelve la conexión
    """
    validate_field_crypto_configuration()
    data_dir().mkdir(parents=True, exist_ok=True)

    target_path = resolve_db_path(sqlite_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    register_sqlite_datetime_codecs()
    con = sqlite3.connect(target_path.as_posix())
    LOGGER.info("db_opened path=%s", target_path)
    con.row_factory = sqlite3.Row
    configure_connection_pii(con)

    _apply_pragmas(con)

    if apply_schema:
        _apply_schema(con)

    return con
