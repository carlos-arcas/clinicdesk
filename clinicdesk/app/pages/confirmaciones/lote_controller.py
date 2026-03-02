from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QWidget

from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.confirmaciones.lote_worker import AccionLoteDTO, WorkerRecordatoriosLote

_COL_CHECK = 0


class GestorLoteConfirmaciones:
    def __init__(self, parent: QWidget, table: QTableWidget, i18n: I18nManager, facade, on_done: Callable[[], None]) -> None:
        self._parent = parent
        self._table = table
        self._i18n = i18n
        self._facade = facade
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

    def actualizar_visibilidad(self) -> None:
        self.barra.setVisible(len(self.selected_ids()) > 0)

    def selected_ids(self) -> tuple[int, ...]:
        result: list[int] = []
        for row in range(self._table.rowCount()):
            item = self._table.item(row, _COL_CHECK)
            if item is None or item.checkState() != Qt.Checked:
                continue
            value = item.data(Qt.UserRole)
            if isinstance(value, int):
                result.append(value)
        return tuple(result)

    def ejecutar(self, tipo: str, canal: str | None) -> None:
        cita_ids = self.selected_ids()
        if not cita_ids:
            return
        if tipo == "ENVIAR" and not self._confirmar_enviado(len(cita_ids)):
            return
        accion = AccionLoteDTO(tipo=tipo, cita_ids=cita_ids, canal=canal)
        self._set_busy(True, tipo)
        self._thread = QThread(self._parent)
        self._worker = WorkerRecordatoriosLote(self._facade, accion)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.ok.connect(self._on_ok)
        self._worker.fail.connect(self._on_fail)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(lambda: self._set_busy(False, tipo))
        self._thread.finished.connect(self._on_done)
        self._thread.start()

    def _confirmar_enviado(self, total: int) -> bool:
        return QMessageBox.question(
            self._parent,
            self._i18n.t("confirmaciones.lote.confirmar_enviado_titulo"),
            self._i18n.t("confirmaciones.lote.confirmar_enviado_texto").format(total=total),
        ) == QMessageBox.Yes

    def _set_busy(self, busy: bool, tipo: str) -> None:
        for btn in (self.btn_whatsapp, self.btn_email, self.btn_enviado):
            btn.setEnabled(not busy)
        if busy:
            key = "confirmaciones.lote.preparando" if tipo == "PREPARAR" else "confirmaciones.lote.guardando"
            self.lbl_estado.setText(self._i18n.t(key))
            return
        self.lbl_estado.setText("")

    def _on_ok(self, dto: ResultadoLoteRecordatoriosDTO) -> None:
        omitidas = dto.omitidas_sin_contacto + dto.omitidas_ya_enviado
        resumen = self._i18n.t("confirmaciones.lote.hecho_resumen").format(hechas=dto.preparadas + dto.enviadas, omitidas=omitidas)
        texto = resumen if omitidas == 0 else f"{resumen}. {self._i18n.t('confirmaciones.lote.omitidas_generico')}"
        QMessageBox.information(self._parent, self._i18n.t("confirmaciones.titulo"), texto)

    def _on_fail(self, error_key: str) -> None:
        QMessageBox.warning(self._parent, self._i18n.t("confirmaciones.titulo"), self._i18n.t(error_key))
