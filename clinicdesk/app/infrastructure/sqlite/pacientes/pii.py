from __future__ import annotations

from clinicdesk.app.infrastructure.sqlite.pii_crypto import PiiCipher


def encrypt_optional(cipher: PiiCipher | None, value: str | None) -> str | None:
    return cipher.encrypt_optional(value) if cipher else value


def decrypt_optional(cipher: PiiCipher | None, value: str | None) -> str | None:
    return cipher.decrypt_optional(value) if cipher else value
