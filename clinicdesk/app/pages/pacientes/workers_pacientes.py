from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot

from clinicdesk.app.ui.workers.listado_async_workers import CargaPacientesWorker


class RelayCargaPacientes(QObject):
    carga_ok = Signal(object, int, object)
    carga_error = Signal(str, int)
    hilo_finalizado = Signal(int)

    def __init__(self, token: int, seleccion_id: int | None) -> None:
        super().__init__()
        self._token = token
        self._seleccion_id = seleccion_id

    @Slot(object)
    def on_worker_ok(self, payload: object) -> None:
        self.carga_ok.emit(payload, self._token, self._seleccion_id)

    @Slot(str)
    def on_worker_error(self, error_type: str) -> None:
        self.carga_error.emit(error_type, self._token)

    @Slot()
    def on_hilo_finalizado(self) -> None:
        self.hilo_finalizado.emit(self._token)


def arrancar_busqueda_rapida(
    *,
    owner: QObject,
    db_path: str,
    activo: bool,
    texto: str,
    on_payload: Callable[[object], None],
    on_thread_finished: Callable[[], None],
) -> QThread:
    thread = QThread(owner)
    worker = CargaPacientesWorker(db_path, activo, texto)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished_ok.connect(on_payload)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(on_thread_finished)
    thread.start()
    return thread


def arrancar_carga(
    *,
    owner: QObject,
    db_path: str,
    activo: bool,
    texto: str,
    token: int,
    seleccion_id: int | None,
    on_ok: Callable[[object, int, int | None], None],
    on_error: Callable[[str, int], None],
    on_thread_finished: Callable[[int], None],
) -> tuple[QThread, CargaPacientesWorker, RelayCargaPacientes]:
    thread = QThread(owner)
    worker = CargaPacientesWorker(db_path, activo, texto)
    relay = RelayCargaPacientes(token=token, seleccion_id=seleccion_id)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished_ok.connect(relay.on_worker_ok)
    worker.finished_error.connect(relay.on_worker_error)
    relay.carga_ok.connect(on_ok)
    relay.carga_error.connect(on_error)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(relay.on_hilo_finalizado)
    relay.hilo_finalizado.connect(on_thread_finished)
    thread.start()
    return thread, worker, relay
