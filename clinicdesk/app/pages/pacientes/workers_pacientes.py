from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget

from clinicdesk.app.ui.workers.listado_async_workers import CargaPacientesWorker


def arrancar_busqueda_rapida(
    *,
    owner: QWidget,
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
    owner: QWidget,
    db_path: str,
    activo: bool,
    texto: str,
    on_ok: Callable[[object], None],
    on_error: Callable[[str], None],
    on_thread_finished: Callable[[], None],
) -> tuple[QThread, CargaPacientesWorker]:
    thread = QThread(owner)
    worker = CargaPacientesWorker(db_path, activo, texto)
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
