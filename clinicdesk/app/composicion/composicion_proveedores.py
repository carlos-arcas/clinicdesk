from __future__ import annotations

import sqlite3

from clinicdesk.app.infrastructure.sqlite.db_path import resolver_db_path_desde_conexion
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo


def build_proveedor_conexion_sqlite_por_hilo(
    connection: sqlite3.Connection,
) -> ProveedorConexionSqlitePorHilo:
    db_path = resolver_db_path_desde_conexion(connection)
    return ProveedorConexionSqlitePorHilo(db_path)
