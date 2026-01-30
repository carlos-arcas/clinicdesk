from __future__ import annotations

from typing import Optional


def normalize_search_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    return text or None


def has_search_values(*values: Optional[str]) -> bool:
    return any(normalize_search_text(v) for v in values)


def like_value(text: str) -> str:
    return f"%{text}%"
