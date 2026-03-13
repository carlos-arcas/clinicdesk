from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Callable


ToastCallback = Callable[[], None]


@dataclass
class ToastPayload:
    tipo: str
    mensaje_key: str
    mensaje: str
    duracion_ms: int
    titulo_key: str | None = None
    titulo: str | None = None
    detalle: str | None = None
    accion_label_key: str | None = None
    accion_label: str | None = None
    accion_callback: ToastCallback | None = None
    on_close: ToastCallback | None = None
    persistente: bool = False
    _accion_ejecutada: bool = False
    _cierre_notificado: bool = False

    @property
    def tiene_detalle(self) -> bool:
        return bool(self.detalle and self.detalle.strip())

    @property
    def tiene_accion(self) -> bool:
        return self.accion_callback is not None and bool(self.accion_label)


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

    def success(
        self,
        key: str,
        *,
        titulo_key: str | None = None,
        detalle: str | None = None,
        accion_label_key: str | None = None,
        accion_callback: ToastCallback | None = None,
        persistente: bool = False,
        duracion_ms: int | None = None,
        on_close: ToastCallback | None = None,
    ) -> ToastPayload:
        return self._encolar(
            "success",
            key,
            titulo_key=titulo_key,
            detalle=detalle,
            accion_label_key=accion_label_key,
            accion_callback=accion_callback,
            persistente=persistente,
            duracion_ms=duracion_ms,
            on_close=on_close,
        )

    def info(
        self,
        key: str,
        *,
        titulo_key: str | None = None,
        detalle: str | None = None,
        accion_label_key: str | None = None,
        accion_callback: ToastCallback | None = None,
        persistente: bool = False,
        duracion_ms: int | None = None,
        on_close: ToastCallback | None = None,
    ) -> ToastPayload:
        return self._encolar(
            "info",
            key,
            titulo_key=titulo_key,
            detalle=detalle,
            accion_label_key=accion_label_key,
            accion_callback=accion_callback,
            persistente=persistente,
            duracion_ms=duracion_ms,
            on_close=on_close,
        )

    def error(
        self,
        key: str,
        *,
        titulo_key: str | None = None,
        detalle: str | None = None,
        accion_label_key: str | None = None,
        accion_callback: ToastCallback | None = None,
        persistente: bool = False,
        duracion_ms: int | None = None,
        on_close: ToastCallback | None = None,
    ) -> ToastPayload:
        return self._encolar(
            "error",
            key,
            titulo_key=titulo_key,
            detalle=detalle,
            accion_label_key=accion_label_key,
            accion_callback=accion_callback,
            persistente=persistente,
            duracion_ms=duracion_ms,
            on_close=on_close,
        )

    def run_current_action(self) -> bool:
        if self._actual is None or not self._actual.tiene_accion:
            return False
        if self._actual._accion_ejecutada:
            return False
        self._actual._accion_ejecutada = True
        assert self._actual.accion_callback is not None
        self._actual.accion_callback()
        self.close_current()
        return True

    def close_current(self) -> None:
        if self._actual is None:
            return
        payload = self._actual
        self._cancelar_timer()
        self._actual = None
        self._notificar_cierre(payload)
        self._notify(None)
        self._mostrar_siguiente()

    def _encolar(
        self,
        tipo: str,
        key: str,
        *,
        titulo_key: str | None = None,
        detalle: str | None = None,
        accion_label_key: str | None = None,
        accion_callback: ToastCallback | None = None,
        persistente: bool = False,
        duracion_ms: int | None = None,
        on_close: ToastCallback | None = None,
    ) -> ToastPayload:
        payload = ToastPayload(
            tipo=tipo,
            mensaje_key=key,
            mensaje=self._traducir(key),
            duracion_ms=max(0, duracion_ms if duracion_ms is not None else self._duracion_ms),
            titulo_key=titulo_key,
            titulo=self._traducir(titulo_key) if titulo_key else None,
            detalle=detalle,
            accion_label_key=accion_label_key,
            accion_label=self._traducir(accion_label_key) if accion_label_key else None,
            accion_callback=accion_callback,
            persistente=persistente,
            on_close=on_close,
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
        if self._programar is not None and not self._actual.persistente and self._actual.duracion_ms > 0:
            self._timer = self._programar(self._actual.duracion_ms, self.close_current)

    def _notificar_cierre(self, payload: ToastPayload) -> None:
        if payload._cierre_notificado or payload.on_close is None:
            return
        payload._cierre_notificado = True
        payload.on_close()

    def _notify(self, payload: ToastPayload | None) -> None:
        for listener in list(self._listeners):
            listener(payload)

    def _cancelar_timer(self) -> None:
        if self._timer is None or self._cancelar is None:
            self._timer = None
            return
        self._cancelar(self._timer)
        self._timer = None
