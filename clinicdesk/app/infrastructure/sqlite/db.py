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

    con = sqlite3.connect(config.db_path.as_posix())
    con.row_factory = sqlite3.Row  # devuelve filas tipo dict-like

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
    con.commit()


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
