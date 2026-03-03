from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget

from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.confirmaciones.lote_resumen import construir_resumen_lote
from clinicdesk.app.pages.confirmaciones.lote_worker import AccionLoteDTO, WorkerRecordatoriosLote

LOGGER = logging.getLogger(__name__)


class GestorLoteConfirmaciones:
    def __init__(
        self,
        parent: QWidget,
        i18n: I18nManager,
        facade,
        *,
        selected_ids: Callable[[], tuple[int, ...]],
        on_done: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._i18n = i18n
        self._facade = facade
        self._selected_ids = selected_ids
        self._on_done = on_done
        self._thread: QThread | None = None
        self._worker: WorkerRecordatoriosLote | None = None
        self.lbl_estado = QLabel()
        self.btn_whatsapp = QPushButton()
        self.btn_email = QPushButton()
        self.btn_enviado = QPushButton()
        self.barra = QWidget(parent)
        lay = QHBoxLayout(self.barra)
        lay.addWidget(self.lbl_estado, 1)
        lay.addWidget(self.btn_whatsapp)
        lay.addWidget(self.btn_email)
        lay.addWidget(self.btn_enviado)
        self.barra.setVisible(False)
        self.btn_whatsapp.clicked.connect(lambda: self.ejecutar("PREPARAR", "WHATSAPP"))
        self.btn_email.clicked.connect(lambda: self.ejecutar("PREPARAR", "EMAIL"))
        self.btn_enviado.clicked.connect(lambda: self.ejecutar("ENVIAR", None))

    def retranslate(self) -> None:
        t = self._i18n.t
        self.btn_whatsapp.setText(t("confirmaciones.lote.preparar_whatsapp"))
        self.btn_email.setText(t("confirmaciones.lote.preparar_correo"))
        self.btn_enviado.setText(t("confirmaciones.lote.marcar_enviado"))

    def actualizar_visibilidad(self, total_seleccionadas: int) -> None:
        self.barra.setVisible(total_seleccionadas > 0)

    def ejecutar(self, tipo: str, canal: str | None) -> None:
        cita_ids = self._selected_ids()
        if not cita_ids:
            return
        if tipo == "ENVIAR" and not self._confirmar_enviado(len(cita_ids)):
            return
        self._log_click(tipo, canal, len(cita_ids))
        self._arrancar_worker(AccionLoteDTO(tipo=tipo, cita_ids=cita_ids, canal=canal))

    def _confirmar_enviado(self, total: int) -> bool:
        return QMessageBox.question(
            self._parent,
            self._i18n.t("confirmaciones.lote.confirmar_enviado_titulo"),
            self._i18n.t("confirmaciones.lote.confirmar_enviado_texto").format(total=total),
        ) == QMessageBox.Yes

    def _arrancar_worker(self, accion: AccionLoteDTO) -> None:
        self._thread = QThread(self._parent)
        self._worker = WorkerRecordatoriosLote(self._facade, accion)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.started.connect(self._on_started)
        self._worker.finished_ok.connect(self._on_ok)
        self._worker.finished_error.connect(self._on_fail)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_done)
        self._thread.start()

    def _on_started(self, operacion: str) -> None:
        for btn in (self.btn_whatsapp, self.btn_email, self.btn_enviado):
            btn.setEnabled(False)
        key = "confirmaciones.lote.preparando" if operacion == "PREPARAR" else "confirmaciones.lote.guardando"
        self.lbl_estado.setText(self._i18n.t(key))

    def _on_ok(self, dto: ResultadoLoteRecordatoriosDTO) -> None:
        for btn in (self.btn_whatsapp, self.btn_email, self.btn_enviado):
            btn.setEnabled(True)
        self.lbl_estado.setText("")
        hechas, omitidas = construir_resumen_lote(dto)
        resumen = self._i18n.t("confirmaciones.lote.hecho_resumen").format(hechas=hechas, omitidas=omitidas)
        texto = resumen if omitidas == 0 else f"{resumen}. {self._i18n.t('confirmaciones.lote.omitidas_generico')}"
        LOGGER.info(
            "confirmaciones_lote_ok",
            extra={
                "action": "confirmaciones_lote_ok",
                "preparadas": dto.preparadas,
                "enviadas": dto.enviadas,
                "omitidas_sin_contacto": dto.omitidas_sin_contacto,
                "omitidas_ya_enviado": dto.omitidas_ya_enviado,
            },
        )
        QMessageBox.information(self._parent, self._i18n.t("confirmaciones.titulo"), texto)

    def _on_fail(self, reason_code: str) -> None:
        for btn in (self.btn_whatsapp, self.btn_email, self.btn_enviado):
            btn.setEnabled(True)
        self.lbl_estado.setText("")
        LOGGER.warning(
            "confirmaciones_lote_fail",
            extra={"action": "confirmaciones_lote_fail", "reason_code": reason_code},
        )
        QMessageBox.warning(self._parent, self._i18n.t("confirmaciones.titulo"), self._i18n.t(reason_code))

    def _log_click(self, operacion: str, canal: str | None, total_seleccionadas: int) -> None:
        LOGGER.info(
            "confirmaciones_lote_click",
            extra={
                "action": "confirmaciones_lote_click",
                "operacion": operacion,
                "canal": canal or "TODOS",
                "total_seleccionadas": total_seleccionadas,
            },
        )
