from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QThread, Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget

from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.confirmaciones.lote_resumen import construir_resumen_lote, construir_texto_resumen_lote
from clinicdesk.app.pages.confirmaciones.lote_worker import (
    AccionLoteDTO,
    RelayOperacionLote,
    WorkerRecordatoriosLote,
    arrancar_worker_lote,
)

LOGGER = logging.getLogger(__name__)


class GestorLoteConfirmaciones:
    def __init__(
        self,
        parent: QWidget,
        i18n: I18nManager,
        facade,
        *,
        selected_ids: Callable[[], tuple[int, ...]],
        on_done: Callable[[int], None],
        contexto_vigente: Callable[[], bool],
    ) -> None:
        self._parent = parent
        self._i18n = i18n
        self._facade = facade
        self._selected_ids = selected_ids
        self._on_done = on_done
        self._contexto_vigente = contexto_vigente
        self._thread: QThread | None = None
        self._worker: WorkerRecordatoriosLote | None = None
        self._relay: RelayOperacionLote | None = None
        self._operacion_actual = 0
        self._operaciones_consumidas: set[int] = set()
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
        if self._thread is not None and self._thread.isRunning():
            LOGGER.info(
                "confirmaciones_lote_omitido",
                extra={"action": "confirmaciones_lote_omitido", "reason": "operacion_en_curso"},
            )
            return
        if tipo == "ENVIAR" and not self._confirmar_enviado(len(cita_ids)):
            return
        self._log_click(tipo, canal, len(cita_ids))
        self._operacion_actual += 1
        self._set_botones_habilitados(False)
        self._arrancar_worker(AccionLoteDTO(tipo=tipo, cita_ids=cita_ids, canal=canal), self._operacion_actual)

    def invalidar_contexto(self) -> None:
        self._operacion_actual += 1
        self._operaciones_consumidas.clear()
        self.lbl_estado.setText("")
        self._set_botones_habilitados(True)

    def _confirmar_enviado(self, total: int) -> bool:
        return (
            QMessageBox.question(
                self._parent,
                self._i18n.t("confirmaciones.lote.confirmar_enviado_titulo"),
                self._i18n.t("confirmaciones.lote.confirmar_enviado_texto").format(total=total),
            )
            == QMessageBox.Yes
        )

    def _arrancar_worker(self, accion: AccionLoteDTO, operation_id: int) -> None:
        self._thread, self._worker, self._relay = arrancar_worker_lote(
            owner=self._parent,
            facade=self._facade,
            accion=accion,
            operation_id=operation_id,
            on_started=self._on_started,
            on_ok=self._on_ok,
            on_error=self._on_fail,
            on_thread_finished=self._on_thread_finished,
        )

    def _set_botones_habilitados(self, habilitado: bool) -> None:
        for btn in (self.btn_whatsapp, self.btn_email, self.btn_enviado):
            btn.setEnabled(habilitado)

    def _es_operacion_vigente(self, operation_id: int) -> bool:
        if operation_id in self._operaciones_consumidas:
            LOGGER.info(
                "confirmaciones_lote_omitido",
                extra={
                    "action": "confirmaciones_lote_omitido",
                    "reason": "operacion_ya_consumida",
                    "operation_id": operation_id,
                },
            )
            return False
        if operation_id != self._operacion_actual:
            LOGGER.info(
                "confirmaciones_lote_omitido",
                extra={
                    "action": "confirmaciones_lote_omitido",
                    "reason": "operacion_obsoleta",
                    "operation_id": operation_id,
                },
            )
            return False
        if not self._contexto_vigente():
            LOGGER.info(
                "confirmaciones_lote_omitido",
                extra={
                    "action": "confirmaciones_lote_omitido",
                    "reason": "contexto_no_vigente",
                    "operation_id": operation_id,
                },
            )
            return False
        return True

    @Slot(str, int)
    def _on_started(self, operacion: str, operation_id: int) -> None:
        if operation_id != self._operacion_actual:
            return
        key = "confirmaciones.lote.preparando" if operacion == "PREPARAR" else "confirmaciones.lote.guardando"
        self.lbl_estado.setText(self._i18n.t(key))

    @Slot(object, int)
    def _on_ok(self, dto: object, operation_id: int) -> None:
        if not isinstance(dto, ResultadoLoteRecordatoriosDTO):
            return
        if not self._es_operacion_vigente(operation_id):
            return
        self._operaciones_consumidas.add(operation_id)
        self.lbl_estado.setText("")
        hechas, omitidas = construir_resumen_lote(dto)
        texto = construir_texto_resumen_lote(hechas, omitidas, self._i18n.t)
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
        self._on_done(operation_id)
        QMessageBox.information(self._parent, self._i18n.t("confirmaciones.titulo"), texto)

    @Slot(str, int)
    def _on_fail(self, reason_code: str, operation_id: int) -> None:
        if not self._es_operacion_vigente(operation_id):
            return
        self._operaciones_consumidas.add(operation_id)
        self.lbl_estado.setText("")
        LOGGER.warning(
            "confirmaciones_lote_fail",
            extra={"action": "confirmaciones_lote_fail", "reason_code": reason_code},
        )
        QMessageBox.warning(self._parent, self._i18n.t("confirmaciones.titulo"), self._i18n.t(reason_code))

    @Slot(int)
    def _on_thread_finished(self, operation_id: int) -> None:
        self._set_botones_habilitados(True)
        self._thread = None
        self._worker = None
        self._relay = None
        if operation_id != self._operacion_actual:
            return
        self.lbl_estado.setText("")
        self._operaciones_consumidas.discard(operation_id)

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
