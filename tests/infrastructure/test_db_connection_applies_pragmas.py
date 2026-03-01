from __future__ import annotations

import sqlite3

from clinicdesk.app.infrastructure.sqlite import db


def test_get_connection_applies_foreign_keys_pragma(monkeypatch) -> None:
    memory_connection = sqlite3.connect(":memory:")

    def _connect(_: str) -> sqlite3.Connection:
        return memory_connection

    monkeypatch.setattr(db.sqlite3, "connect", _connect)

    connection = db.get_connection("ignored.sqlite")

    foreign_keys = connection.execute("PRAGMA foreign_keys;").fetchone()[0]
    assert foreign_keys == 1

    connection.close()
