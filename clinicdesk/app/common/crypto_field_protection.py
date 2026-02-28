from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import subprocess
import unicodedata
from typing import Optional

_KEY_ENV = "CLINICDESK_FIELD_KEY"
_HASH_KEY_ENV = "CLINICDESK_FIELD_HASH_KEY"
_FLAG_ENV = "CLINICDESK_FIELD_CRYPTO"
_MIN_KEY_LEN = 32


def field_crypto_enabled() -> bool:
    return os.getenv(_FLAG_ENV, "0").strip() == "1"


def encrypt(value: str) -> str:
    plaintext = _require_value(value)
    passphrase = _passphrase(_KEY_ENV)
    encrypted = _run_gpg(
        [
            "gpg",
            "--batch",
            "--yes",
            "--pinentry-mode",
            "loopback",
            "--passphrase",
            passphrase,
            "--cipher-algo",
            "AES256",
            "--compress-algo",
            "none",
            "--symmetric",
            "--output",
            "-",
        ],
        plaintext.encode("utf-8"),
    )
    return base64.urlsafe_b64encode(encrypted).decode("ascii")


def decrypt(value: str) -> str:
    payload = _require_value(value)
    raw = base64.urlsafe_b64decode(payload.encode("ascii"))
    passphrase = _passphrase(_KEY_ENV)
    plaintext = _run_gpg(
        [
            "gpg",
            "--batch",
            "--yes",
            "--pinentry-mode",
            "loopback",
            "--passphrase",
            passphrase,
            "--decrypt",
            "--output",
            "-",
        ],
        raw,
    )
    return plaintext.decode("utf-8")


def hash_lookup(value: str) -> str:
    key = _load_binary_key(_HASH_KEY_ENV, fallback_env=_KEY_ENV)
    normalized = _normalize_for_lookup(value)
    digest = hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")


def normalize_lookup_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = _normalize_for_lookup(value)
    return normalized or None


def normalize_phone_lookup(value: Optional[str]) -> Optional[str]:
    normalized = normalize_lookup_value(value)
    if not normalized:
        return None
    compact = re.sub(r"[\s\-().]", "", normalized)
    return compact or None


def _run_gpg(command: list[str], payload: bytes) -> bytes:
    proc = subprocess.run(command, input=payload, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError("Field encryption command failed")
    return proc.stdout


def _passphrase(env_name: str) -> str:
    key = _load_binary_key(env_name)
    return base64.urlsafe_b64encode(key).decode("ascii")


def _load_binary_key(env_name: str, *, fallback_env: Optional[str] = None) -> bytes:
    encoded = os.getenv(env_name, "").strip()
    if not encoded and fallback_env:
        encoded = os.getenv(fallback_env, "").strip()
    if not encoded:
        raise RuntimeError(f"Missing required env var: {env_name}")

    raw = _decode_key(encoded)
    if len(raw) < _MIN_KEY_LEN:
        raise RuntimeError(f"{env_name} must be at least {_MIN_KEY_LEN} bytes")
    return raw[:32]


def _decode_key(encoded: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(encoded.encode("ascii"))
    except Exception:
        return encoded.encode("utf-8")


def _require_value(value: str) -> str:
    if value is None:
        raise ValueError("Value cannot be None")
    if not isinstance(value, str):
        raise TypeError("Value must be str")
    return value


def _normalize_for_lookup(value: str) -> str:
    raw = _require_value(value)
    normalized = unicodedata.normalize("NFKC", raw).strip().casefold()
    return re.sub(r"\s+", " ", normalized)
