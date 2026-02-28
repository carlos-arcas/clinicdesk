from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    locked: bool = False


class AuthService:
    def __init__(self, connection: sqlite3.Connection, *, max_attempts: int = 5, lock_seconds: int = 60) -> None:
        self._con = connection
        self._max_attempts = max_attempts
        self._lock_seconds = lock_seconds
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._con.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash BLOB NOT NULL,
                password_salt BLOB NOT NULL,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._con.commit()

    def has_users(self) -> bool:
        row = self._con.execute("SELECT COUNT(*) AS c FROM auth_users").fetchone()
        return bool(row[0])

    def create_user(self, username: str, password: str) -> None:
        username = username.strip()
        digest, salt = _hash_password(password)
        now = _utc_now_iso()
        self._con.execute(
            """
            INSERT INTO auth_users(username, password_hash, password_salt, failed_attempts, locked_until, created_at, updated_at)
            VALUES (?, ?, ?, 0, NULL, ?, ?)
            """,
            (username, digest, salt, now, now),
        )
        self._con.commit()

    def verify(self, username: str, password: str) -> AuthResult:
        row = self._con.execute(
            "SELECT id, password_hash, password_salt, failed_attempts, locked_until FROM auth_users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
        if row is None:
            return AuthResult(ok=False)

        user_id = int(row["id"])
        locked_until = row["locked_until"]
        if locked_until and datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
            return AuthResult(ok=False, locked=True)

        expected_hash = bytes(row["password_hash"])
        salt = bytes(row["password_salt"])
        computed = _derive_hash(password, salt)
        if hmac.compare_digest(expected_hash, computed):
            self._con.execute(
                "UPDATE auth_users SET failed_attempts = 0, locked_until = NULL, updated_at = ? WHERE id = ?",
                (_utc_now_iso(), user_id),
            )
            self._con.commit()
            return AuthResult(ok=True)

        failed_attempts = int(row["failed_attempts"]) + 1
        lock_until_value = None
        if failed_attempts >= self._max_attempts:
            lock_until_value = (datetime.now(timezone.utc) + timedelta(seconds=self._lock_seconds)).isoformat()
            failed_attempts = 0
        self._con.execute(
            "UPDATE auth_users SET failed_attempts = ?, locked_until = ?, updated_at = ? WHERE id = ?",
            (failed_attempts, lock_until_value, _utc_now_iso(), user_id),
        )
        self._con.commit()
        return AuthResult(ok=False, locked=lock_until_value is not None)


def is_demo_mode_allowed(db_path: Path) -> bool:
    normalized = db_path.resolve()
    data_root = Path("./data").resolve()
    return normalized.is_relative_to(data_root) or "demo" in normalized.name.lower()


def _hash_password(password: str) -> tuple[bytes, bytes]:
    salt = os.urandom(16)
    return _derive_hash(password, salt), salt


def _derive_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
