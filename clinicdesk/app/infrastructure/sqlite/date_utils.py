from __future__ import annotations

from datetime import date
from typing import Optional


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def format_iso_date(value: Optional[date]) -> Optional[str]:
    return value.isoformat() if value else None
