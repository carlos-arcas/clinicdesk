from __future__ import annotations

import re

_PHONE_SEPARATORS = re.compile(r"[\s().-]+")


def canonicalize_sensitive_value(field: str, value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if field == "documento":
        return cleaned.replace(" ", "").replace("-", "").upper()
    if field == "email":
        return cleaned.lower()
    if field == "telefono":
        compact = _PHONE_SEPARATORS.sub("", cleaned)
        return "".join(ch for ch in compact if ch.isdigit())
    return " ".join(cleaned.split())


def canonicalize_for_lookup(field: str, value: str | None) -> str | None:
    return canonicalize_sensitive_value(field, value)


__all__ = ["canonicalize_for_lookup", "canonicalize_sensitive_value"]
