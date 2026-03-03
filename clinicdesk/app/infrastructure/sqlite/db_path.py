from __future__ import annotations

import sqlite3


def resolver_db_path_desde_conexion(conexion: sqlite3.Connection) -> str:
    row = conexion.execute("PRAGMA database_list").fetchone()
    return str(row[2]) if row and row[2] else ":memory:"
