from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget

from clinicdesk.app.application.confirmaciones import FiltrosConfirmacionesDTO, PaginacionConfirmacionesDTO
from clinicdesk.app.ui.workers.listado_async_workers import CargaConfirmacionesWorker


def arrancar_busqueda_rapida(
    *,
    owner: QWidget,
    db_path: str,
    filtros: FiltrosConfirmacionesDTO,
    page_size: int,
    riesgo_uc: object,
    salud_uc: object,
    on_payload: Callable[[object], None],
    on_thread_finished: Callable[[], None],
) -> QThread:
    thread = QThread(owner)
    worker = CargaConfirmacionesWorker(
        db_path=db_path,
        filtros=filtros,
        paginacion=PaginacionConfirmacionesDTO(limit=page_size, offset=0),
        riesgo_uc=riesgo_uc,
        salud_uc=salud_uc,
    )
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
    owner: QWidget,
    db_path: str,
    filtros: FiltrosConfirmacionesDTO,
    page_size: int,
    offset: int,
    riesgo_uc: object,
    salud_uc: object,
    on_ok: Callable[[object], None],
    on_error: Callable[[str], None],
    on_thread_finished: Callable[[], None],
) -> tuple[QThread, CargaConfirmacionesWorker]:
    thread = QThread(owner)
    worker = CargaConfirmacionesWorker(
        db_path=db_path,
        filtros=filtros,
        paginacion=PaginacionConfirmacionesDTO(limit=page_size, offset=offset),
        riesgo_uc=riesgo_uc,
        salud_uc=salud_uc,
    )
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished_ok.connect(on_ok)
    worker.finished_error.connect(on_error)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(on_thread_finished)
    thread.start()
    return thread, worker
