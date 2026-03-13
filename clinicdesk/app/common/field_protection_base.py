from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable

from clinicdesk.app.common.crypto_field_protection import decrypt, encrypt, hash_lookup
from clinicdesk.app.common.sensitive_field_canonicalization import canonicalize_sensitive_value


@dataclass(frozen=True)
class ProtectedFieldValue:
    legacy: str | None
    encrypted: str | None
    lookup_hash: str | None


class FieldProtectionBase:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        table_name: str,
        fields: Iterable[str],
        fields_not_null_legacy: Iterable[str],
        enabled_flag: bool,
    ) -> None:
        self._table_name = table_name
        self._fields = frozenset(fields)
        self._fields_not_null_legacy = frozenset(fields_not_null_legacy)
        self._enabled = enabled_flag
        self._has_columns = self.schema_supports_columns(connection)

    @property
    def enabled(self) -> bool:
        return self._enabled and self._has_columns

    @property
    def has_columns(self) -> bool:
        return self._has_columns

    def encode(self, field: str, value: str | None) -> ProtectedFieldValue:
        canonical = canonicalize_sensitive_value(field, value)
        if not self.enabled or field not in self._fields or canonical is None:
            return ProtectedFieldValue(legacy=value, encrypted=None, lookup_hash=None)
        lookup = hash_lookup(canonical, field=field)
        legacy = lookup if field in self._fields_not_null_legacy else None
        return ProtectedFieldValue(legacy=legacy, encrypted=encrypt(canonical), lookup_hash=lookup)

    def decode(self, field: str, *, legacy: str | None, encrypted: str | None) -> str | None:
        if field not in self._fields:
            return legacy
        if encrypted:
            return decrypt(encrypted)
        return legacy

    def hash_for_lookup(self, field: str, value: str | None) -> str | None:
        canonical = canonicalize_sensitive_value(field, value)
        if not self.enabled or field not in self._fields or canonical is None:
            return None
        return hash_lookup(canonical, field=field)

    def schema_supports_columns(self, connection: sqlite3.Connection) -> bool:
        columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({self._table_name})")}
        return self.required_crypto_columns().issubset(columns)

    def required_crypto_columns(self) -> set[str]:
        required: set[str] = set()
        for field in self._fields:
            required.add(f"{field}_enc")
            required.add(f"{field}_hash")
        return required
