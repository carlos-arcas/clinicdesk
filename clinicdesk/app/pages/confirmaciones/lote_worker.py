from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal, Slot

from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO


@dataclass(frozen=True, slots=True)
class AccionLoteDTO:
    tipo: str
    cita_ids: tuple[int, ...]
    canal: str | None = None


class WorkerRecordatoriosLote(QObject):
    started = Signal(str)
    finished_ok = Signal(object)
    finished_error = Signal(str)
    finished = Signal()

    def __init__(self, facade, accion: AccionLoteDTO) -> None:
        super().__init__()
        self._facade = facade
        self._accion = accion

    def run(self) -> None:
        try:
            self.started.emit(self._accion.tipo)
            self.finished_ok.emit(self._resolver_accion())
        except Exception:
            self.finished_error.emit("confirmaciones.lote.error_accionable")
        finally:
            self._facade.cerrar_conexion_hilo_actual()
            self.finished.emit()

    def _resolver_accion(self) -> ResultadoLoteRecordatoriosDTO:
        if self._accion.tipo == "PREPARAR":
            return self._facade.preparar_lote_uc.ejecutar(self._accion.cita_ids, self._accion.canal or "WHATSAPP")
        return self._facade.marcar_enviado_lote_uc.ejecutar(self._accion.cita_ids, self._accion.canal)


class RelayOperacionLote(QObject):
    started = Signal(str, int)
    ok = Signal(object, int)
    error = Signal(str, int)
    hilo_finalizado = Signal(int)

    def __init__(self, operation_id: int) -> None:
        super().__init__()
        self._operation_id = operation_id

    @Slot(str)
    def on_started(self, operacion: str) -> None:
        self.started.emit(operacion, self._operation_id)

    @Slot(object)
    def on_ok(self, payload: object) -> None:
        self.ok.emit(payload, self._operation_id)

    @Slot(str)
    def on_error(self, reason_code: str) -> None:
        self.error.emit(reason_code, self._operation_id)

    @Slot()
    def on_thread_finished(self) -> None:
        self.hilo_finalizado.emit(self._operation_id)


def arrancar_worker_lote(
    *,
    owner: QObject,
    facade: object,
    accion: AccionLoteDTO,
    operation_id: int,
    on_started: Callable[[str, int], None],
    on_ok: Callable[[object, int], None],
    on_error: Callable[[str, int], None],
    on_thread_finished: Callable[[int], None],
) -> tuple[QThread, WorkerRecordatoriosLote, RelayOperacionLote]:
    thread = QThread(owner)
    worker = WorkerRecordatoriosLote(facade, accion)
    relay = RelayOperacionLote(operation_id=operation_id)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.started.connect(relay.on_started)
    worker.finished_ok.connect(relay.on_ok)
    worker.finished_error.connect(relay.on_error)
    relay.started.connect(on_started)
    relay.ok.connect(on_ok)
    relay.error.connect(on_error)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(relay.on_thread_finished)
    relay.hilo_finalizado.connect(on_thread_finished)
    thread.start()
    return thread, worker, relay
