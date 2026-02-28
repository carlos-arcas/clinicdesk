from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from clinicdesk.app.common.crypto_field_protection import decrypt, encrypt, hash_lookup
from clinicdesk.app.common.field_crypto_flags import pacientes_field_crypto_enabled

_PROTECTED = {"documento", "email", "telefono", "direccion"}


@dataclass(frozen=True)
class ProtectedFieldValue:
    legacy: str | None
    encrypted: str | None
    lookup_hash: str | None


class PacientesFieldProtection:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._enabled = pacientes_field_crypto_enabled()
        self._has_columns = _has_crypto_columns(connection)

    @property
    def enabled(self) -> bool:
        return self._enabled and self._has_columns

    @property
    def has_columns(self) -> bool:
        return self._has_columns

    def encode(self, field: str, value: str | None) -> ProtectedFieldValue:
        if not self.enabled or field not in _PROTECTED or value is None:
            return ProtectedFieldValue(legacy=value, encrypted=None, lookup_hash=None)
        return ProtectedFieldValue(
            legacy=None,
            encrypted=encrypt(value),
            lookup_hash=hash_lookup(value),
        )

    def decode(self, field: str, *, legacy: str | None, encrypted: str | None) -> str | None:
        if field not in _PROTECTED:
            return legacy
        if encrypted:
            return decrypt(encrypted)
        return legacy

    def hash_for_lookup(self, field: str, value: str | None) -> str | None:
        if not self.enabled or field not in _PROTECTED or value is None:
            return None
        return hash_lookup(value)


def _has_crypto_columns(connection: sqlite3.Connection) -> bool:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(pacientes)").fetchall()
    }
    required = {
        "documento_enc",
        "documento_hash",
        "email_enc",
        "email_hash",
        "telefono_enc",
        "telefono_hash",
        "direccion_enc",
        "direccion_hash",
    }
    return required.issubset(columns)
