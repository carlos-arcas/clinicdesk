from __future__ import annotations

from pathlib import Path
import sqlite3
import threading

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.infrastructure.sqlite.db import get_connection


LOGGER = get_logger(__name__)


class ProveedorConexionSqlitePorHilo:
    """Entrega una conexión SQLite por hilo para evitar uso cruzado entre threads."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._local = threading.local()

    def obtener(self) -> sqlite3.Connection:
        conexion = getattr(self._local, "conexion", None)
        if conexion is None:
            conexion = get_connection(self._db_path)
            self._local.conexion = conexion
            LOGGER.debug(
                "sqlite_conexion_hilo_creada",
                extra={
                    "action": "sqlite_conexion_hilo_creada",
                    "db_path": self._db_path.as_posix(),
                    "thread_name": threading.current_thread().name,
                    "thread_id": threading.get_ident(),
                },
            )
        return conexion

    def cerrar_conexion_del_hilo_actual(self) -> None:
        conexion = getattr(self._local, "conexion", None)
        if conexion is None:
            return
        try:
            conexion.close()
        finally:
            del self._local.conexion

