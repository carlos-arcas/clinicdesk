from __future__ import annotations

import logging

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox

from clinicdesk.app.pages.confirmaciones.lote_worker import AccionLoteDTO, WorkerRecordatoriosLote

LOGGER = logging.getLogger(__name__)


def preparar_whatsapp_rapido(page, item) -> None:
    if page._cita_en_preparacion is not None:
        return
    page._cita_en_preparacion = item.cita_id
    page._vm.set_processing()
    page._load_data(reset=False)
    page._registrar_telemetria("confirmaciones_whatsapp_rapido", "click", item.cita_id)
    page._thread_rapido = QThread(page)
    accion = AccionLoteDTO(tipo="PREPARAR", cita_ids=(item.cita_id,), canal="WHATSAPP")
    page._worker_rapido = WorkerRecordatoriosLote(page._container.recordatorios_citas_facade, accion)
    page._worker_rapido.moveToThread(page._thread_rapido)
    page._thread_rapido.started.connect(page._worker_rapido.run)
    page._worker_rapido.finished_ok.connect(page._on_whatsapp_rapido_ok)
    page._worker_rapido.finished_error.connect(page._on_whatsapp_rapido_fail)
    page._worker_rapido.finished.connect(page._thread_rapido.quit)
    page._worker_rapido.finished.connect(page._worker_rapido.deleteLater)
    page._thread_rapido.finished.connect(page._thread_rapido.deleteLater)
    page._thread_rapido.start()


def on_whatsapp_rapido_ok(page) -> None:
    page._registrar_telemetria("confirmaciones_whatsapp_rapido", "ok", page._cita_en_preparacion)
    page._cita_en_preparacion = None
    page._load_data(reset=False)
    QMessageBox.information(
        page,
        page._i18n.t("confirmaciones.titulo"),
        page._i18n.t("confirmaciones.accion.hecho"),
    )
    page._ui.table.setFocus()


def on_whatsapp_rapido_fail(page, reason_code: str) -> None:
    LOGGER.warning(
        "confirmaciones_whatsapp_rapido_fail",
        extra={"action": "confirmaciones_whatsapp_rapido_fail", "reason_code": reason_code},
    )
    page._registrar_telemetria("confirmaciones_whatsapp_rapido", "fail", page._cita_en_preparacion)
    page._cita_en_preparacion = None
    page._load_data(reset=False)
    QMessageBox.warning(
        page,
        page._i18n.t("confirmaciones.titulo"),
        page._i18n.t("confirmaciones.accion.error_guardar"),
    )
    page._ui.table.setFocus()
