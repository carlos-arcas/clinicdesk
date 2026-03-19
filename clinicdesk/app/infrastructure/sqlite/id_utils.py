from __future__ import annotations

import sqlite3


class SqliteIntegrityError(RuntimeError):
    """Error de contrato al leer ids persistidos en SQLite."""


def require_entero_sqlite(value: object, *, context: str) -> int:
    if type(value) is int:
        return value
    raise SqliteIntegrityError(f"{context}: se esperaba un entero SQLite válido y se recibió {value!r}.")


def require_lastrowid(cursor: sqlite3.Cursor, *, context: str) -> int:
    return require_entero_sqlite(cursor.lastrowid, context=context)


def require_row_id(row: sqlite3.Row, *, context: str, column: str = "id") -> int:
    return require_entero_sqlite(row[column], context=f"{context}.{column}")
