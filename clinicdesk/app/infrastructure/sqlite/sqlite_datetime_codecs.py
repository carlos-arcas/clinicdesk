from __future__ import annotations

import sqlite3
from datetime import date, datetime, time


_CODECS_REGISTERED = False


def register_sqlite_datetime_codecs() -> None:
    """Registra adapters/converters explícitos para evitar APIs por defecto deprecadas."""
    global _CODECS_REGISTERED
    if _CODECS_REGISTERED:
        return
    sqlite3.register_adapter(datetime, adapt_datetime)
    sqlite3.register_adapter(date, adapt_date)
    sqlite3.register_adapter(time, adapt_time)
    sqlite3.register_converter("datetime", convert_datetime)
    sqlite3.register_converter("timestamp", convert_datetime)
    sqlite3.register_converter("date", convert_date)
    sqlite3.register_converter("time", convert_time)
    _CODECS_REGISTERED = True


def adapt_datetime(value: datetime) -> str:
    return value.isoformat(sep=" ")


def convert_datetime(value: bytes) -> datetime:
    return datetime.fromisoformat(value.decode("utf-8"))


def adapt_date(value: date) -> str:
    return value.isoformat()


def convert_date(value: bytes) -> date:
    return date.fromisoformat(value.decode("utf-8"))


def adapt_time(value: time) -> str:
    return value.isoformat()


def convert_time(value: bytes) -> time:
    return time.fromisoformat(value.decode("utf-8"))


def serialize_datetime(value: datetime) -> str:
    return adapt_datetime(value)


def deserialize_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
