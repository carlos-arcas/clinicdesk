from __future__ import annotations

import sqlite3


_PROTECTED_COLUMNS = ("documento", "email", "telefono", "direccion")


def ensure_pacientes_field_crypto_columns(con: sqlite3.Connection) -> None:
    _ensure_table_field_crypto_columns(con, table="pacientes")


def ensure_medicos_field_crypto_columns(con: sqlite3.Connection) -> None:
    _ensure_table_field_crypto_columns(con, table="medicos")


def ensure_personal_field_crypto_columns(con: sqlite3.Connection) -> None:
    _ensure_table_field_crypto_columns(con, table="personal")


def _ensure_table_field_crypto_columns(con: sqlite3.Connection, *, table: str) -> None:
    columns = _table_columns(con, table=table)
    for name in _PROTECTED_COLUMNS:
        _ensure_text_column(con, columns, table=table, column=f"{name}_enc")
        _ensure_text_column(con, columns, table=table, column=f"{name}_hash")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_{name}_hash ON {table}({name}_hash)")


def _table_columns(con: sqlite3.Connection, *, table: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def _ensure_text_column(
    con: sqlite3.Connection,
    columns: set[str],
    *,
    table: str,
    column: str,
) -> None:
    if column in columns:
        return
    con.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
    columns.add(column)
