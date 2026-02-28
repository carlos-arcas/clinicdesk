from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


@contextmanager
def sqlite_seed_turbo(connection: sqlite3.Connection) -> Iterator[None]:
    previous = _read_restoreable_pragmas(connection)
    _apply_seed_pragmas(connection)
    LOGGER.info("seed_turbo_mode_enabled")
    try:
        yield
    finally:
        _restore_pragmas(connection, previous)
        LOGGER.info("seed_turbo_mode_restored")


def _apply_seed_pragmas(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA synchronous=NORMAL;")
    connection.execute("PRAGMA temp_store=MEMORY;")
    connection.execute("PRAGMA cache_size=-20000;")
    connection.execute("PRAGMA foreign_keys=ON;")


def _read_restoreable_pragmas(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        "synchronous": _read_pragma_int(connection, "synchronous"),
        "temp_store": _read_pragma_int(connection, "temp_store"),
        "cache_size": _read_pragma_int(connection, "cache_size"),
    }


def _restore_pragmas(connection: sqlite3.Connection, pragmas: dict[str, int]) -> None:
    for key in ("synchronous", "temp_store", "cache_size"):
        connection.execute(f"PRAGMA {key}={pragmas[key]};")


def _read_pragma_int(connection: sqlite3.Connection, pragma: str) -> int:
    row = connection.execute(f"PRAGMA {pragma};").fetchone()
    if row is None:
        raise ValueError(f"No se pudo leer PRAGMA {pragma}")
    return int(row[0])
