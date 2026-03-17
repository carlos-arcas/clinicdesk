from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot


@dataclass(frozen=True, slots=True)
class ErrorEntrenamientoOperativo:
    tipo: str
    mensaje: str


class WorkerEntrenarOperativo(QObject):
    started = Signal()
    ok = Signal(object)
    fail = Signal(object)
    finished = Signal()

    def __init__(self, ejecutar: Callable[[], object], cerrar_conexion: Callable[[], None] | None = None) -> None:
        super().__init__()
        self._ejecutar = ejecutar
        self._cerrar_conexion = cerrar_conexion

    def run(self) -> None:
        self.started.emit()
        try:
            self.ok.emit(self._ejecutar())
        except Exception as exc:  # noqa: BLE001
            self.fail.emit(ErrorEntrenamientoOperativo(type(exc).__name__, str(exc)))
        finally:
            if self._cerrar_conexion:
                self._cerrar_conexion()
            self.finished.emit()


class RelayEntrenamientoOperativo(QObject):
    ok = Signal(str, int, object)
    fail = Signal(str, int, object)
    hilo_finalizado = Signal(str, int)

    def __init__(self, tipo: str, token: int) -> None:
        super().__init__()
        self._tipo = tipo
        self._token = token

    @Slot(object)
    def on_worker_ok(self, payload: object) -> None:
        self.ok.emit(self._tipo, self._token, payload)

    @Slot(object)
    def on_worker_fail(self, payload: object) -> None:
        self.fail.emit(self._tipo, self._token, payload)

    @Slot()
    def on_hilo_finalizado(self) -> None:
        self.hilo_finalizado.emit(self._tipo, self._token)
