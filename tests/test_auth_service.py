import sqlite3

from clinicdesk.app.security.auth import AuthService


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    return con


def test_hash_and_verify_roundtrip() -> None:
    con = _con()
    service = AuthService(con)
    service.create_user("admin", "s3cret")

    row = con.execute("SELECT password_hash, password_salt FROM auth_users WHERE username='admin'").fetchone()
    assert row is not None
    assert bytes(row["password_hash"]) != b"s3cret"
    assert bytes(row["password_salt"]) != b""

    assert service.verify("admin", "s3cret").ok is True
    assert service.verify("admin", "bad").ok is False


def test_lock_after_failed_attempts() -> None:
    service = AuthService(_con(), max_attempts=2, lock_seconds=600)
    service.create_user("admin", "s3cret")

    assert service.verify("admin", "bad").ok is False
    locked = service.verify("admin", "bad")
    assert locked.ok is False
    assert locked.locked is True

    still_locked = service.verify("admin", "s3cret")
    assert still_locked.ok is False
    assert still_locked.locked is True
