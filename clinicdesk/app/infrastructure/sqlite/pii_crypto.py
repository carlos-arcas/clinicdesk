from __future__ import annotations

import base64
import hashlib
import hmac
import os
import sqlite3
from dataclasses import dataclass
from typing import Iterable


_ENV_ENABLED = "CLINICDESK_PII_ENCRYPTION_ENABLED"
_ENV_KEY = "CLINICDESK_PII_ENCRYPTION_KEY"
_PREFIX = "enc:v1:"

_CONNECTION_CIPHERS: dict[int, "PiiCipher"] = {}


@dataclass(frozen=True)
class PiiEncryptionSettings:
    enabled: bool
    key_material: str | None


class PiiCipher:
    def __init__(self, key_material: str) -> None:
        self._enc_key = _derive_key(key_material, purpose="enc")
        self._mac_key = _derive_key(key_material, purpose="mac")

    def encrypt_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        return self.encrypt(value)

    def decrypt_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        return self.decrypt(value)

    def encrypt(self, value: str) -> str:
        if value.startswith(_PREFIX):
            return value
        nonce = os.urandom(16)
        plaintext = value.encode("utf-8")
        ciphertext = _xor_keystream(plaintext, self._enc_key, nonce)
        tag = hmac.new(self._mac_key, nonce + ciphertext, hashlib.sha256).digest()[:16]
        blob = base64.urlsafe_b64encode(nonce + ciphertext + tag).decode("ascii")
        return f"{_PREFIX}{blob}"

    def decrypt(self, value: str) -> str:
        if not value.startswith(_PREFIX):
            return value
        payload = value[len(_PREFIX):]
        raw = base64.urlsafe_b64decode(payload.encode("ascii"))
        if len(raw) < 32:
            raise ValueError("Encrypted payload is malformed.")
        nonce = raw[:16]
        tag = raw[-16:]
        ciphertext = raw[16:-16]
        expected = hmac.new(self._mac_key, nonce + ciphertext, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(tag, expected):
            raise ValueError("Encrypted payload authentication failed.")
        plaintext = _xor_keystream(ciphertext, self._enc_key, nonce)
        return plaintext.decode("utf-8")


def encryption_settings_from_env() -> PiiEncryptionSettings:
    raw_enabled = os.getenv(_ENV_ENABLED, "false").strip().lower()
    enabled = raw_enabled in {"1", "true", "yes", "on"}
    key_material = os.getenv(_ENV_KEY)
    if enabled and not key_material:
        raise RuntimeError(
            "PII encryption is enabled but CLINICDESK_PII_ENCRYPTION_KEY is not set. "
            "Set the env var or disable CLINICDESK_PII_ENCRYPTION_ENABLED."
        )
    return PiiEncryptionSettings(enabled=enabled, key_material=key_material)


def configure_connection_pii(connection: sqlite3.Connection) -> None:
    settings = encryption_settings_from_env()
    _CONNECTION_CIPHERS.pop(id(connection), None)
    if settings.enabled and settings.key_material:
        _CONNECTION_CIPHERS[id(connection)] = PiiCipher(settings.key_material)


def get_connection_pii_cipher(connection: sqlite3.Connection) -> PiiCipher | None:
    return _CONNECTION_CIPHERS.get(id(connection))


def cleanup_connection_pii(connection: sqlite3.Connection) -> None:
    _CONNECTION_CIPHERS.pop(id(connection), None)


def migrate_existing_pii_data(connection: sqlite3.Connection) -> None:
    cipher = get_connection_pii_cipher(connection)
    if cipher is None:
        return
    plans = {
        "pacientes": ("telefono", "email", "direccion", "alergias", "observaciones"),
        "medicos": ("telefono", "email", "direccion"),
        "personal": ("telefono", "email", "direccion"),
    }
    for table, columns in plans.items():
        _migrate_table_columns(connection, table=table, columns=columns, cipher=cipher)


def _migrate_table_columns(
    connection: sqlite3.Connection,
    *,
    table: str,
    columns: Iterable[str],
    cipher: PiiCipher,
) -> None:
    select_columns = ", ".join(["id", *columns])
    rows = connection.execute(f"SELECT {select_columns} FROM {table}").fetchall()
    for row in rows:
        updates: list[str] = []
        values: list[str] = []
        for column in columns:
            raw_value = row[column]
            if raw_value is None:
                continue
            encrypted = cipher.encrypt(str(raw_value))
            if encrypted == raw_value:
                continue
            updates.append(f"{column} = ?")
            values.append(encrypted)
        if not updates:
            continue
        values.append(row["id"])
        sql = f"UPDATE {table} SET {', '.join(updates)} WHERE id = ?"
        connection.execute(sql, values)


def _derive_key(key_material: str, *, purpose: str) -> bytes:
    return hashlib.sha256(f"{purpose}:{key_material}".encode("utf-8")).digest()


def _xor_keystream(data: bytes, key: bytes, nonce: bytes) -> bytes:
    output = bytearray(len(data))
    counter = 0
    offset = 0
    while offset < len(data):
        block = hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest()
        chunk = data[offset : offset + len(block)]
        for index, value in enumerate(chunk):
            output[offset + index] = value ^ block[index]
        offset += len(block)
        counter += 1
    return bytes(output)
