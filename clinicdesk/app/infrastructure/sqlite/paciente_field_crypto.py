from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from clinicdesk.app.common.crypto_field_protection import (
    decrypt,
    encrypt,
    field_crypto_enabled,
    hash_lookup,
    normalize_lookup_value,
    normalize_phone_lookup,
)


@dataclass(frozen=True, slots=True)
class ProtectedPacienteFields:
    documento_enc: Optional[str]
    documento_hash: Optional[str]
    email_enc: Optional[str]
    email_hash: Optional[str]
    telefono_enc: Optional[str]
    telefono_hash: Optional[str]
    direccion_enc: Optional[str]


def build_protected_fields(
    *, documento: str, email: Optional[str], telefono: Optional[str], direccion: Optional[str]
) -> ProtectedPacienteFields:
    if not field_crypto_enabled():
        return ProtectedPacienteFields(None, None, None, None, None, None, None)

    email_value = normalize_lookup_value(email) if email else None
    phone_value = normalize_phone_lookup(telefono) if telefono else None
    return ProtectedPacienteFields(
        documento_enc=encrypt(documento),
        documento_hash=hash_lookup(documento),
        email_enc=encrypt(email) if email else None,
        email_hash=hash_lookup(email_value) if email_value else None,
        telefono_enc=encrypt(telefono) if telefono else None,
        telefono_hash=hash_lookup(phone_value) if phone_value else None,
        direccion_enc=encrypt(direccion) if direccion else None,
    )


def resolve_field(*, legacy: Optional[str], encrypted: Optional[str]) -> Optional[str]:
    if field_crypto_enabled() and encrypted:
        return decrypt(encrypted)
    return legacy


def documento_hash_for_query(value: Optional[str]) -> Optional[str]:
    normalized = normalize_lookup_value(value)
    if not normalized:
        return None
    return hash_lookup(normalized)


def email_hash_for_query(value: Optional[str]) -> Optional[str]:
    normalized = normalize_lookup_value(value)
    if not normalized:
        return None
    return hash_lookup(normalized)


def telefono_hash_for_query(value: Optional[str]) -> Optional[str]:
    normalized = normalize_phone_lookup(value)
    if not normalized:
        return None
    return hash_lookup(normalized)
