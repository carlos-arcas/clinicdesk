from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_REDACTED = "***"

_EMAIL_RE = re.compile(r"(?P<user>[A-Za-z0-9._%+-]+)@(?P<domain>[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_DNI_RE = re.compile(r"\b\d{7,8}[A-Za-z]?\b")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)")

_SENSITIVE_KEY_PARTS = (
    "dni",
    "documento",
    "telefono",
    "teléfono",
    "phone",
    "email",
    "correo",
    "mail",
    "nombre",
    "name",
)


def redact_text(value: str) -> str:
    redacted = _EMAIL_RE.sub(lambda _: _REDACTED, value)
    redacted = _DNI_RE.sub(_REDACTED, redacted)
    redacted = _PHONE_RE.sub(_REDACTED, redacted)
    return redacted


def redact_value(value: Any, *, key: str | None = None) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        if key and _is_sensitive_key(key):
            return _REDACTED
        return redact_text(value)
    if isinstance(value, Mapping):
        return {k: redact_value(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [redact_value(item, key=key) for item in value]
    return value


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in _SENSITIVE_KEY_PARTS)
