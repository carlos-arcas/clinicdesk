# infrastructure/sqlite/db.py
"""
Conexión y bootstrap de SQLite.

Responsabilidades:
- Abrir conexión con SQLite con PRAGMAs recomendados.
- Aplicar el schema desde un archivo .sql (idempotente: CREATE IF NOT EXISTS).
- Centralizar el acceso para que el resto de capas no repitan lógica.

Notas:
- foreign_keys debe activarse por conexión en SQLite.
- WAL mejora concurrencia (lecturas mientras se escribe).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from clinicdesk.app.infrastructure.sqlite.sqlite_datetime_codecs import (
    register_sqlite_datetime_codecs,
)
from clinicdesk.app.infrastructure.sqlite.field_crypto_migrations import (
    ensure_pacientes_field_crypto_columns,
)
from clinicdesk.app.infrastructure.sqlite.pii_crypto import (
    configure_connection_pii,
    migrate_existing_pii_data,
)


@dataclass(frozen=True)
class SqliteConfig:
    """
    Configuración para SQLite.
    - db_path: ruta al archivo .sqlite/.db
    - schema_path: ruta al schema.sql
    """
    db_path: Path
    schema_path: Path


def connect(config: SqliteConfig) -> sqlite3.Connection:
    """
    Abre conexión SQLite y aplica PRAGMAs recomendados.
    """
    config.db_path.parent.mkdir(parents=True, exist_ok=True)
    register_sqlite_datetime_codecs()

    con = sqlite3.connect(config.db_path.as_posix())
    con.row_factory = sqlite3.Row  # devuelve filas tipo dict-like
    configure_connection_pii(con)

    _apply_pragmas(con)
    return con


def _apply_pragmas(con: sqlite3.Connection) -> None:
    """
    PRAGMAs por conexión.

    foreign_keys:
    - Obligatorio para que se respeten las FKs.

    journal_mode=WAL:
    - Mejora concurrencia (muy útil en apps con UI).

    synchronous=NORMAL:
    - Buen equilibrio seguridad/rendimiento para apps de escritorio.
    """
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")
    con.execute("PRAGMA temp_store = MEMORY;")
    # con.execute("PRAGMA busy_timeout = 5000;")  # opcional, útil si hay locks


def apply_schema(con: sqlite3.Connection, schema_path: Path) -> None:
    """
    Aplica el schema desde un archivo .sql.

    Requisitos:
    - El schema debe ser idempotente (CREATE TABLE IF NOT EXISTS...).
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"No existe schema.sql en: {schema_path}")

    sql = schema_path.read_text(encoding="utf-8")

    # executescript permite ejecutar múltiples sentencias SQL separadas por ';'
    con.executescript(sql)
    _migrate_stock_columns(con)
    _migrate_active_columns(con)
    _migrate_demo_columns(con)
    ensure_pacientes_field_crypto_columns(con)
    migrate_existing_pii_data(con)
    con.commit()


def _migrate_stock_columns(con: sqlite3.Connection) -> None:
    """
    Migra columnas legacy de stock si existen en la base de datos.
    """
    _ensure_stock_column(con, table="medicamentos")
    _ensure_stock_column(con, table="materiales")


def _migrate_active_columns(con: sqlite3.Connection) -> None:
    _ensure_flag_column(con, table="citas", column="activo")
    _ensure_flag_column(con, table="ausencias_medico", column="activo")
    _ensure_flag_column(con, table="ausencias_personal", column="activo")
    _ensure_flag_column(con, table="recetas", column="activo")
    _ensure_flag_column(con, table="receta_lineas", column="activo")
    _ensure_flag_column(con, table="dispensaciones", column="activo")
    _ensure_flag_column(con, table="movimientos_medicamentos", column="activo")
    _ensure_flag_column(con, table="movimientos_materiales", column="activo")
    _ensure_flag_column(con, table="incidencias", column="activo")
    _ensure_flag_column(con, table="salas", column="activa")
    _ensure_flag_column(con, table="turnos", column="activo")


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


def _ensure_flag_column(con: sqlite3.Connection, *, table: str, column: str) -> None:
    columns = {
        row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column in columns:
        return
    con.execute(
        f"ALTER TABLE {table} ADD COLUMN {column} INTEGER NOT NULL DEFAULT 1"
    )
    con.execute(
        f"UPDATE {table} SET {column} = 1"
    )


def _migrate_demo_columns(con: sqlite3.Connection) -> None:
    _ensure_text_column(con, table="recetas", column="estado", default="ACTIVA")
    _ensure_int_column(con, table="receta_lineas", column="cantidad", default=1)
    _ensure_int_column(con, table="receta_lineas", column="pendiente", default=1)
    _ensure_text_column(con, table="receta_lineas", column="estado", default="PENDIENTE")
    _ensure_text_column(con, table="movimientos_medicamentos", column="referencia", default="")
    _ensure_text_column(con, table="movimientos_materiales", column="referencia", default="")


def _ensure_text_column(con: sqlite3.Connection, *, table: str, column: str, default: str) -> None:
    columns = {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
    if column in columns:
        return
    escaped = default.replace("'", "''")
    con.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT NOT NULL DEFAULT '{escaped}'")


def _ensure_int_column(con: sqlite3.Connection, *, table: str, column: str, default: int) -> None:
    columns = {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
    if column in columns:
        return
    con.execute(f"ALTER TABLE {table} ADD COLUMN {column} INTEGER NOT NULL DEFAULT {int(default)}")


def bootstrap(
    db_path: str | Path,
    schema_path: str | Path,
    *,
    apply: bool = True,
) -> sqlite3.Connection:
    """
    Atajo para:
    - conectar
    - aplicar schema (si apply=True)
    """
    cfg = SqliteConfig(db_path=Path(db_path), schema_path=Path(schema_path))
    con = connect(cfg)
    if apply:
        apply_schema(con, cfg.schema_path)
    return con
