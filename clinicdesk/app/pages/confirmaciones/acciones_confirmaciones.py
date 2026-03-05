from __future__ import annotations


def set_busy(parent, activo: bool, mensaje_key: str) -> None:
    handler = getattr(parent.window(), "set_busy", None)
    if callable(handler):
        handler(activo, mensaje_key)


def toast_success(parent, key: str) -> None:
    handler = getattr(parent.window(), "toast_success", None)
    if callable(handler):
        handler(key)


def toast_info(parent, key: str) -> None:
    handler = getattr(parent.window(), "toast_info", None)
    if callable(handler):
        handler(key)


def toast_error(parent, key: str) -> None:
    handler = getattr(parent.window(), "toast_error", None)
    if callable(handler):
        handler(key)


def navegar_prediccion(parent) -> None:
    window = parent.window()
    if hasattr(window, "navigate"):
        window.navigate("prediccion_ausencias")
