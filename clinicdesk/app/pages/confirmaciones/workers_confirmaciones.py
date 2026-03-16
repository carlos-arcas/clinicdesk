from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot

from clinicdesk.app.application.confirmaciones import FiltrosConfirmacionesDTO, PaginacionConfirmacionesDTO
from clinicdesk.app.ui.workers.listado_async_workers import CargaConfirmacionesWorker


class RelayConfirmaciones(QObject):
    carga_ok = Signal(object, int)
    carga_error = Signal(str, int)
    busqueda_ok = Signal(object, int)
    busqueda_error = Signal(str, int)
    hilo_carga_finalizado = Signal(int)
    hilo_busqueda_finalizado = Signal(int)

    def __init__(self, token: int) -> None:
        super().__init__()
        self._token = token

    @Slot(object)
    def on_worker_carga_ok(self, payload: object) -> None:
        self.carga_ok.emit(payload, self._token)

    @Slot(str)
    def on_worker_carga_error(self, error_type: str) -> None:
        self.carga_error.emit(error_type, self._token)

    @Slot(object)
    def on_worker_busqueda_ok(self, payload: object) -> None:
        self.busqueda_ok.emit(payload, self._token)

    @Slot(str)
    def on_worker_busqueda_error(self, error_type: str) -> None:
        self.busqueda_error.emit(error_type, self._token)

    @Slot()
    def on_hilo_carga_finalizado(self) -> None:
        self.hilo_carga_finalizado.emit(self._token)

    @Slot()
    def on_hilo_busqueda_finalizado(self) -> None:
        self.hilo_busqueda_finalizado.emit(self._token)


def arrancar_busqueda_rapida(
    *,
    owner: QObject,
    db_path: str,
    filtros: FiltrosConfirmacionesDTO,
    page_size: int,
    riesgo_uc: object,
    salud_uc: object,
    token: int,
    on_payload: Callable[[object, int], None],
    on_error: Callable[[str, int], None],
    on_thread_finished: Callable[[int], None],
) -> tuple[QThread, CargaConfirmacionesWorker, RelayConfirmaciones]:
    thread = QThread(owner)
    worker = CargaConfirmacionesWorker(
        db_path=db_path,
        filtros=filtros,
        paginacion=PaginacionConfirmacionesDTO(limit=page_size, offset=0),
        riesgo_uc=riesgo_uc,
        salud_uc=salud_uc,
    )
    relay = RelayConfirmaciones(token=token)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished_ok.connect(relay.on_worker_busqueda_ok)
    worker.finished_error.connect(relay.on_worker_busqueda_error)
    relay.busqueda_ok.connect(on_payload)
    relay.busqueda_error.connect(on_error)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(relay.on_hilo_busqueda_finalizado)
    relay.hilo_busqueda_finalizado.connect(on_thread_finished)
    thread.start()
    return thread, worker, relay


def arrancar_carga(
    *,
    owner: QObject,
    db_path: str,
    filtros: FiltrosConfirmacionesDTO,
    page_size: int,
    offset: int,
    riesgo_uc: object,
    salud_uc: object,
    token: int,
    on_ok: Callable[[object, int], None],
    on_error: Callable[[str, int], None],
    on_thread_finished: Callable[[int], None],
) -> tuple[QThread, CargaConfirmacionesWorker, RelayConfirmaciones]:
    thread = QThread(owner)
    worker = CargaConfirmacionesWorker(
        db_path=db_path,
        filtros=filtros,
        paginacion=PaginacionConfirmacionesDTO(limit=page_size, offset=offset),
        riesgo_uc=riesgo_uc,
        salud_uc=salud_uc,
    )
    relay = RelayConfirmaciones(token=token)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished_ok.connect(relay.on_worker_carga_ok)
    worker.finished_error.connect(relay.on_worker_carga_error)
    relay.carga_ok.connect(on_ok)
    relay.carga_error.connect(on_error)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(relay.on_hilo_carga_finalizado)
    relay.hilo_carga_finalizado.connect(on_thread_finished)
    thread.start()
    return thread, worker, relay
