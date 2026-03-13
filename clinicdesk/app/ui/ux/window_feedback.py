from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QWidget


def set_busy(window_parent: QWidget, activo: bool, mensaje_key: str) -> None:
    callback = getattr(window_parent.window(), "set_busy", None)
    if callable(callback):
        callback(activo, mensaje_key)


def toast_success(window_parent: QWidget, key: str, **kwargs: Any) -> None:
    callback = getattr(window_parent.window(), "toast_success", None)
    if callable(callback):
        callback(key, **kwargs)


def toast_info(window_parent: QWidget, key: str, **kwargs: Any) -> None:
    callback = getattr(window_parent.window(), "toast_info", None)
    if callable(callback):
        callback(key, **kwargs)


def toast_error(window_parent: QWidget, key: str, **kwargs: Any) -> None:
    callback = getattr(window_parent.window(), "toast_error", None)
    if callable(callback):
        callback(key, **kwargs)
