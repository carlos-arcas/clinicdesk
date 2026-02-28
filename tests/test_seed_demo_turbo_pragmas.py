from __future__ import annotations

import sqlite3

from clinicdesk.app.infrastructure.sqlite.sqlite_tuning import sqlite_seed_turbo


def _pragma_int(connection: sqlite3.Connection, key: str) -> int:
    row = connection.execute(f"PRAGMA {key};").fetchone()
    assert row is not None
    return int(row[0])


def test_sqlite_seed_turbo_applies_and_restores_pragmas(tmp_path) -> None:
    db_file = tmp_path / "seed_turbo.db"
    connection = sqlite3.connect(db_file.as_posix())
    try:
        connection.execute("PRAGMA synchronous=FULL;")
        connection.execute("PRAGMA temp_store=DEFAULT;")
        connection.execute("PRAGMA cache_size=1500;")
        previous = {
            "synchronous": _pragma_int(connection, "synchronous"),
            "temp_store": _pragma_int(connection, "temp_store"),
            "cache_size": _pragma_int(connection, "cache_size"),
        }

        with sqlite_seed_turbo(connection):
            assert _pragma_int(connection, "synchronous") == 1
            assert _pragma_int(connection, "temp_store") == 2
            assert _pragma_int(connection, "cache_size") == -20000
            assert _pragma_int(connection, "foreign_keys") == 1

        assert _pragma_int(connection, "synchronous") == previous["synchronous"]
        assert _pragma_int(connection, "temp_store") == previous["temp_store"]
        assert _pragma_int(connection, "cache_size") == previous["cache_size"]
    finally:
        connection.close()
