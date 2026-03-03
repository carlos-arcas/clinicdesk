from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, Signal


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
