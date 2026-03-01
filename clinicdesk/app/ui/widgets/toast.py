"""API de toasts con compatibilidad retro para callers legacy."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class GestorToasts:
    """Gestor de notificaciones toast independiente de Qt para facilitar tests."""

    def __init__(self) -> None:
        self._notificaciones: list[dict[str, Any]] = []

    @property
    def notificaciones(self) -> list[dict[str, Any]]:
        """Expone notificaciones emitidas para inspección en tests."""
        return self._notificaciones

    def _emitir(
        self,
        tipo: str,
        message: str,
        *,
        title: str | None = None,
        action_label: str | None = None,
        action_callback: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload = {
            "tipo": tipo,
            "message": message,
            "title": title,
            "action_label": action_label,
            "action_callback": action_callback,
            "meta": kwargs,
        }
        self._notificaciones.append(payload)
        return payload

    def success(
        self,
        message: str,
        *,
        title: str | None = None,
        action_label: str | None = None,
        action_callback: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self._emitir(
            "success",
            message,
            title=title,
            action_label=action_label,
            action_callback=action_callback,
            **kwargs,
        )

    def error(
        self,
        message: str,
        *,
        title: str | None = None,
        action_label: str | None = None,
        action_callback: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self._emitir(
            "error",
            message,
            title=title,
            action_label=action_label,
            action_callback=action_callback,
            **kwargs,
        )


class ToastManager(GestorToasts):
    """Alias retrocompatible de :class:`GestorToasts`."""

    def success(
        self,
        message: str,
        *,
        title: str | None = None,
        action_label: str | None = None,
        action_callback: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return super().success(
            message,
            title=title,
            action_label=action_label,
            action_callback=action_callback,
            **kwargs,
        )

    def error(
        self,
        message: str,
        *,
        title: str | None = None,
        action_label: str | None = None,
        action_callback: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return super().error(
            message,
            title=title,
            action_label=action_label,
            action_callback=action_callback,
            **kwargs,
        )


__all__ = ["GestorToasts", "ToastManager"]
