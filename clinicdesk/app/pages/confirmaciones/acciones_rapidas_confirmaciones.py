from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from clinicdesk.app.pages.confirmaciones.lote_worker import AccionLoteDTO, WorkerRecordatoriosLote

LOGGER = logging.getLogger(__name__)


class RelayAccionRapidaConfirmaciones(QObject):
    ok = Signal(object, int)
    error = Signal(str, int)
    hilo_finalizado = Signal(int)

    def __init__(self, operation_id: int) -> None:
        super().__init__()
        self._operation_id = operation_id

    @Slot(object)
    def on_ok(self, payload: object) -> None:
        self.ok.emit(payload, self._operation_id)

    @Slot(str)
    def on_error(self, reason_code: str) -> None:
        self.error.emit(reason_code, self._operation_id)

    @Slot()
    def on_thread_finished(self) -> None:
        self.hilo_finalizado.emit(self._operation_id)


def arrancar_preparacion_whatsapp(
    *,
    owner: QObject,
    facade: object,
    cita_id: int,
    operation_id: int,
    on_ok: Callable[[object, int], None],
    on_error: Callable[[str, int], None],
    on_thread_finished: Callable[[int], None],
) -> tuple[QThread, WorkerRecordatoriosLote, RelayAccionRapidaConfirmaciones]:
    thread = QThread(owner)
    accion = AccionLoteDTO(tipo="PREPARAR", cita_ids=(cita_id,), canal="WHATSAPP")
    worker = WorkerRecordatoriosLote(facade, accion)
    relay = RelayAccionRapidaConfirmaciones(operation_id=operation_id)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished_ok.connect(relay.on_ok)
    worker.finished_error.connect(relay.on_error)
    relay.ok.connect(on_ok)
    relay.error.connect(on_error)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(relay.on_thread_finished)
    relay.hilo_finalizado.connect(on_thread_finished)
    thread.start()
    return thread, worker, relay


def preparar_whatsapp_rapido(page, item) -> None:
    if page._cita_en_preparacion is not None:
        return
    page._token_whatsapp_rapido += 1
    operation_id = page._token_whatsapp_rapido
    page._cita_en_preparacion = item.cita_id
    page._solicitar_refresh_operativo(origen="whatsapp_rapido_inicio", operation_id=operation_id)
    page._registrar_telemetria("confirmaciones_whatsapp_rapido", "click", item.cita_id)
    page._thread_rapido, page._worker_rapido, page._relay_rapido = arrancar_preparacion_whatsapp(
        owner=page,
        facade=page._container.recordatorios_citas_facade,
        cita_id=item.cita_id,
        operation_id=operation_id,
        on_ok=page._on_whatsapp_rapido_ok,
        on_error=page._on_whatsapp_rapido_fail,
        on_thread_finished=page._on_whatsapp_rapido_thread_finished,
    )


def on_whatsapp_rapido_ok(page, operation_id: int) -> None:
    if not page._es_whatsapp_rapido_vigente(operation_id):
        return
    page._registrar_telemetria("confirmaciones_whatsapp_rapido", "ok", page._cita_en_preparacion)
    page._cita_en_preparacion = None
    page._solicitar_refresh_operativo(origen="whatsapp_rapido_ok", operation_id=operation_id)
    if not page._puede_mostrar_feedback_operativo(operation_id):
        return
    QMessageBox.information(
        page,
        page._i18n.t("confirmaciones.titulo"),
        page._i18n.t("confirmaciones.accion.hecho"),
    )


def on_whatsapp_rapido_fail(page, reason_code: str, operation_id: int) -> None:
    if not page._es_whatsapp_rapido_vigente(operation_id):
        return
    LOGGER.warning(
        "confirmaciones_whatsapp_rapido_fail",
        extra={
            "action": "confirmaciones_whatsapp_rapido_fail",
            "reason_code": reason_code,
            "operation_id": operation_id,
        },
    )
    page._registrar_telemetria("confirmaciones_whatsapp_rapido", "fail", page._cita_en_preparacion)
    page._cita_en_preparacion = None
    page._solicitar_refresh_operativo(origen="whatsapp_rapido_fail", operation_id=operation_id)
    if not page._puede_mostrar_feedback_operativo(operation_id):
        return
    QMessageBox.warning(
        page,
        page._i18n.t("confirmaciones.titulo"),
        page._i18n.t("confirmaciones.accion.error_guardar"),
    )
