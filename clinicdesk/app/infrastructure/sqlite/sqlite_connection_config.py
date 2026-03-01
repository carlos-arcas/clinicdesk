from __future__ import annotations

import sqlite3


def configurar_conexion(connection: sqlite3.Connection) -> None:
    """Aplica PRAGMAs recomendados para cada conexión SQLite."""
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA journal_mode = WAL;")
    connection.execute("PRAGMA synchronous = NORMAL;")
    connection.execute("PRAGMA temp_store = MEMORY;")

