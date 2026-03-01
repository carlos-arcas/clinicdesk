from __future__ import annotations

import sqlite3
from pathlib import Path

from clinicdesk.app.infrastructure.sqlite.sqlite_datetime_codecs import (
    register_sqlite_datetime_codecs,
)
from clinicdesk.app.infrastructure.sqlite.sqlite_connection_config import (
    configurar_conexion,
)


def obtener_conexion(db_path: str = "data/clinicdesk.sqlite") -> sqlite3.Connection:
    """
    Crea y devuelve una conexión SQLite configurada.

    sqlite3.connect(path):
      - Abre (o crea) un fichero .sqlite.
      - Devuelve un objeto Connection que permite ejecutar SQL.

    row_factory = sqlite3.Row:
      - Hace que cada fila devuelta por fetchall() se pueda acceder como dict:
        fila["id"] en vez de fila[0].

    PRAGMA foreign_keys = ON:
      - Activa claves foráneas en SQLite (por defecto puede estar desactivado).
    """
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    register_sqlite_datetime_codecs()
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    configurar_conexion(conn)
    return conn


def inicializar_bd(conexion: sqlite3.Connection) -> None:
    """
    Crea tablas si no existen.

    conexion.execute(sql):
      - Ejecuta una sentencia SQL.
    conexion.commit():
      - Confirma cambios (INSERT/UPDATE/CREATE TABLE).
    """
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL
        )
        """
    )

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY (id_paciente) REFERENCES pacientes(id) ON DELETE CASCADE
        )
        """
    )

    conexion.commit()
