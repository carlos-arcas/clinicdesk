from __future__ import annotations

import base64
import os

from clinicdesk.app.common.crypto_field_protection import decrypt, encrypt, hash_lookup


def _set_keys() -> None:
    raw = b"a" * 32
    os.environ["CLINICDESK_FIELD_KEY"] = base64.urlsafe_b64encode(raw).decode("ascii")
    os.environ["CLINICDESK_FIELD_HASH_KEY"] = base64.urlsafe_b64encode(b"b" * 32).decode("ascii")


def test_encrypt_decrypt_roundtrip() -> None:
    _set_keys()
    plaintext = "ana@example.test"
    encrypted = encrypt(plaintext)
    assert encrypted != plaintext
    assert decrypt(encrypted) == plaintext


def test_encrypt_uses_random_nonce() -> None:
    _set_keys()
    plaintext = "644-123-987"
    first = encrypt(plaintext)
    second = encrypt(plaintext)
    assert first != second
    assert decrypt(first) == plaintext
    assert decrypt(second) == plaintext


def test_hash_lookup_is_stable_after_normalization() -> None:
    _set_keys()
    assert hash_lookup("  Ana@Example.Test  ") == hash_lookup("ana@example.test")
