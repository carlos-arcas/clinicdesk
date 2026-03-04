from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToastPayload:
    tipo: str
    mensaje_key: str
    mensaje: str
    duracion_ms: int


class ToastManager:
    """Gestor de toasts reutilizable e independiente de Qt."""

    def __init__(
        self,
        *,
        traducir: Callable[[str], str] | None = None,
        duracion_ms: int = 2500,
        programar: Callable[[int, Callable[[], None]], Any] | None = None,
        cancelar: Callable[[Any], None] | None = None,
    ) -> None:
        self._traducir = traducir or (lambda key: key)
        self._duracion_ms = duracion_ms
        self._programar = programar
        self._cancelar = cancelar
        self._cola: deque[ToastPayload] = deque()
        self._actual: ToastPayload | None = None
        self._timer: Any | None = None
        self._listeners: list[Callable[[ToastPayload | None], None]] = []

    @property
    def actual(self) -> ToastPayload | None:
        return self._actual

    def subscribe(self, listener: Callable[[ToastPayload | None], None]) -> None:
        self._listeners.append(listener)

    def success(self, key: str) -> ToastPayload:
        return self._encolar("success", key)

    def info(self, key: str) -> ToastPayload:
        return self._encolar("info", key)

    def error(self, key: str) -> ToastPayload:
        return self._encolar("error", key)

    def close_current(self) -> None:
        if self._actual is None:
            return
        self._cancelar_timer()
        self._actual = None
        self._notify(None)
        self._mostrar_siguiente()

    def _encolar(self, tipo: str, key: str) -> ToastPayload:
        payload = ToastPayload(
            tipo=tipo,
            mensaje_key=key,
            mensaje=self._traducir(key),
            duracion_ms=self._duracion_ms,
        )
        self._cola.append(payload)
        if self._actual is None:
            self._mostrar_siguiente()
        return payload

    def _mostrar_siguiente(self) -> None:
        if self._actual is not None or not self._cola:
            return
        self._actual = self._cola.popleft()
        self._notify(self._actual)
        if self._programar is not None:
            self._timer = self._programar(self._actual.duracion_ms, self.close_current)

    def _notify(self, payload: ToastPayload | None) -> None:
        for listener in list(self._listeners):
            listener(payload)

    def _cancelar_timer(self) -> None:
        if self._timer is None or self._cancelar is None:
            self._timer = None
            return
        self._cancelar(self._timer)
        self._timer = None
