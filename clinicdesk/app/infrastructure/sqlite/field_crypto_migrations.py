from __future__ import annotations

import sqlite3


_PROTECTED_COLUMNS = ("documento", "email", "telefono", "direccion")


def ensure_pacientes_field_crypto_columns(con: sqlite3.Connection) -> None:
    columns = _table_columns(con, table="pacientes")
    for name in _PROTECTED_COLUMNS:
        _ensure_text_column(con, columns, table="pacientes", column=f"{name}_enc")
        _ensure_text_column(con, columns, table="pacientes", column=f"{name}_hash")
        con.execute(
            f"CREATE INDEX IF NOT EXISTS idx_pacientes_{name}_hash ON pacientes({name}_hash)"
        )


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
