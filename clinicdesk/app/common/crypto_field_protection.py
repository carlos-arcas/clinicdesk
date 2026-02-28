from __future__ import annotations

import base64
import hashlib
import hmac
import os

_ENV_KEY = "CLINICDESK_CRYPTO_KEY"
_VERSION = "cfp:v1:"


def encrypt(value: str) -> str:
    if value.startswith(_VERSION):
        return value
    aesgcm = _aesgcm()
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
    payload = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return f"{_VERSION}{payload}"


def decrypt(value: str) -> str:
    if not value.startswith(_VERSION):
        return value
    aesgcm = _aesgcm()
    raw = base64.urlsafe_b64decode(value[len(_VERSION) :].encode("ascii"))
    nonce, ciphertext = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def hash_lookup(value: str) -> str:
    normalized = _normalize_lookup(value)
    digest = hmac.new(_lookup_key(), normalized.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")


def _aesgcm():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing dependency: cryptography") from exc
    return AESGCM(_encryption_key())


def _encryption_key() -> bytes:
    return hashlib.sha256(_key_material().encode("utf-8")).digest()


def _lookup_key() -> bytes:
    material = f"lookup:{_key_material()}".encode("utf-8")
    return hashlib.sha256(material).digest()


def _key_material() -> str:
    key = os.getenv(_ENV_KEY, "").strip()
    if not key:
        raise RuntimeError("CLINICDESK_CRYPTO_KEY is required for field protection.")
    return key


def _normalize_lookup(value: str) -> str:
    return " ".join(value.strip().lower().split())
