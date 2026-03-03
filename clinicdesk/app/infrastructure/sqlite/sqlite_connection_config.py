from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path


_WAL_CONFIGURED_PATHS: set[str] = set()
_WAL_LOCKS_BY_PATH: dict[str, threading.Lock] = {}
_WAL_LOCKS_MUTEX = threading.Lock()
_WAL_MAX_ATTEMPTS = 3
_WAL_RETRY_DELAYS_SECONDS = (0.01, 0.03, 0.05)


def _normalizar_db_path(db_path: str | Path) -> str:
    return Path(db_path).expanduser().resolve().as_posix()


def _obtener_lock_por_path(path_normalizado: str) -> threading.Lock:
    with _WAL_LOCKS_MUTEX:
        lock = _WAL_LOCKS_BY_PATH.get(path_normalizado)
        if lock is None:
            lock = threading.Lock()
            _WAL_LOCKS_BY_PATH[path_normalizado] = lock
        return lock


def _es_operational_error_por_bloqueo(exc: sqlite3.OperationalError) -> bool:
    return "database is locked" in str(exc).lower()


def _aplicar_wal_con_reintentos(connection: sqlite3.Connection) -> None:
    ultimo_error: sqlite3.OperationalError | None = None
    for intentos in range(_WAL_MAX_ATTEMPTS):
        try:
            connection.execute("PRAGMA journal_mode = WAL;")
            return
        except sqlite3.OperationalError as exc:
            if not _es_operational_error_por_bloqueo(exc):
                raise
            ultimo_error = exc
            if intentos == _WAL_MAX_ATTEMPTS - 1:
                raise
            time.sleep(_WAL_RETRY_DELAYS_SECONDS[intentos])
    if ultimo_error is not None:
        raise ultimo_error


def configurar_conexion(
    connection: sqlite3.Connection,
    db_path: str | Path | None = None,
) -> None:
    """Aplica PRAGMAs recomendados para cada conexión SQLite."""
    if db_path is not None:
        path_normalizado = _normalizar_db_path(db_path)
        lock = _obtener_lock_por_path(path_normalizado)
        with lock:
            if path_normalizado not in _WAL_CONFIGURED_PATHS:
                _aplicar_wal_con_reintentos(connection)
                _WAL_CONFIGURED_PATHS.add(path_normalizado)
    else:
        _aplicar_wal_con_reintentos(connection)

    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA busy_timeout = 5000;")
    connection.execute("PRAGMA synchronous = NORMAL;")
    connection.execute("PRAGMA temp_store = MEMORY;")
