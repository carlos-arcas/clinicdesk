from __future__ import annotations

import base64
import hashlib
import hmac
import os

_ENV_KEY = "CLINICDESK_CRYPTO_KEY"
_ENV_KEY_PREVIOUS = "CLINICDESK_CRYPTO_KEY_PREVIOUS"
_VERSION = "cfp:v1:"


class CryptoFieldProtectionError(RuntimeError):
    """Error controlado para cifrado/descifrado de campos protegidos."""


def encrypt(value: str) -> str:
    if value.startswith(_VERSION):
        return value
    aesgcm = _aesgcm(_active_key_material())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
    payload = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return f"{_VERSION}{payload}"


def decrypt(value: str) -> str:
    if not value.startswith(_VERSION):
        return value
    raw = _decode_payload(value)
    nonce, ciphertext = raw[:12], raw[12:]
    materials = [_active_key_material(), *_previous_key_materials()]
    last_error: Exception | None = None
    for material in materials:
        try:
            aesgcm = _aesgcm(material)
            return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as exc:
            if not _is_invalid_tag_error(exc):
                raise CryptoFieldProtectionError("No se pudo descifrar campo protegido.") from exc
            last_error = exc
    raise CryptoFieldProtectionError("No se pudo descifrar campo protegido.") from last_error


def hash_lookup(value: str) -> str:
    normalized = _normalize_lookup(value)
    digest = hmac.new(_lookup_key(), normalized.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")


def _aesgcm(material: str):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency: cryptography. Install requirements.txt (pip install -r requirements.txt)."
        ) from exc
    return AESGCM(_encryption_key(material))


def _encryption_key(material: str) -> bytes:
    return hashlib.sha256(material.encode("utf-8")).digest()


def _lookup_key() -> bytes:
    material = f"lookup:{_active_key_material()}".encode("utf-8")
    return hashlib.sha256(material).digest()


def _active_key_material() -> str:
    key = os.getenv(_ENV_KEY, "").strip()
    if not key:
        raise RuntimeError("CLINICDESK_CRYPTO_KEY is required for field protection.")
    return key


def _previous_key_materials() -> list[str]:
    key = os.getenv(_ENV_KEY_PREVIOUS, "").strip()
    if not key:
        return []
    return [key]


def _decode_payload(value: str) -> bytes:
    try:
        raw = base64.urlsafe_b64decode(value[len(_VERSION) :].encode("ascii"))
    except Exception as exc:
        raise CryptoFieldProtectionError("Token cifrado inválido.") from exc
    if len(raw) < 13:
        raise CryptoFieldProtectionError("Token cifrado inválido.")
    return raw


def _is_invalid_tag_error(exc: Exception) -> bool:
    try:
        from cryptography.exceptions import InvalidTag
    except ModuleNotFoundError:
        return False
    return isinstance(exc, InvalidTag)


def _normalize_lookup(value: str) -> str:
    return " ".join(value.strip().lower().split())
