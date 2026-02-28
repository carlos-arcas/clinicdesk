from __future__ import annotations

import sqlite3

from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


def log_screen_data_loaded(connection: sqlite3.Connection, module: str, count: int) -> None:
    db_path = ""
    try:
        row = connection.execute("PRAGMA database_list").fetchone()
        db_path = row[2] if row else ""
    except sqlite3.Error:
        db_path = ""
    LOGGER.info("screen_data_loaded module=%s count=%s db_path=%s", module, count, db_path)
