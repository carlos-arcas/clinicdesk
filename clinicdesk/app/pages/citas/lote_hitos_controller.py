from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget

from clinicdesk.app.application.citas import HitoAtencion, ModoTimestampHito, ResultadoLoteHitosDTO
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.lote_hitos_estado import estado_boton_hito_lote
from clinicdesk.app.pages.citas.lote_hitos_resumen import construir_resumen_hitos_lote
from clinicdesk.app.pages.citas.lote_hitos_worker import AccionLoteHitosDTO, WorkerHitosLote

LOGGER = get_logger(__name__)


class GestorLoteHitosCitas:
    def __init__(
        self,
        parent: QWidget,
        i18n: I18nManager,
        db_path: str,
        *,
        selected_ids: Callable[[], tuple[int, ...]],
        on_done: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._i18n = i18n
        self._db_path = db_path
        self._selected_ids = selected_ids
        self._on_done = on_done
        self._thread: QThread | None = None
        self._worker: WorkerHitosLote | None = None
        self.lbl_estado = QLabel()
        self.lbl_modo = QLabel()
        self.combo_modo = QComboBox()
        self.btn_llegada = QPushButton()
        self.btn_inicio = QPushButton()
        self.btn_fin = QPushButton()
        self.btn_salida = QPushButton()
        self.barra = QWidget(parent)
        lay = QHBoxLayout(self.barra)
        lay.addWidget(self.lbl_estado, 1)
        lay.addWidget(self.lbl_modo)
        lay.addWidget(self.combo_modo)
        lay.addWidget(self.btn_llegada)
        lay.addWidget(self.btn_inicio)
        lay.addWidget(self.btn_fin)
        lay.addWidget(self.btn_salida)
        self.barra.setVisible(False)
        self._cargar_modos()
        self.combo_modo.currentIndexChanged.connect(self._actualizar_estado_botones)
        self.btn_llegada.clicked.connect(lambda: self.ejecutar(HitoAtencion.CHECK_IN))
        self.btn_inicio.clicked.connect(lambda: self.ejecutar(HitoAtencion.INICIO_CONSULTA))
        self.btn_fin.clicked.connect(lambda: self.ejecutar(HitoAtencion.FIN_CONSULTA))
        self.btn_salida.clicked.connect(lambda: self.ejecutar(HitoAtencion.CHECK_OUT))

    def retranslate(self) -> None:
        t = self._i18n.t
        self.lbl_modo.setText(t("citas.hitos.lote.modo_etiqueta"))
        self.btn_llegada.setText(t("citas.hitos.marcar_llegada"))
        self.btn_inicio.setText(t("citas.hitos.iniciar_consulta"))
        self.btn_fin.setText(t("citas.hitos.finalizar_consulta"))
        self.btn_salida.setText(t("citas.hitos.marcar_salida"))
        self._cargar_modos()
        self._actualizar_estado_botones()

    def actualizar_visibilidad(self, total_seleccionadas: int, filtro_calidad_activo: bool) -> None:
        self.lbl_estado.setText(self._i18n.t("citas.hitos.lote.seleccionadas_x").format(total=total_seleccionadas))
        self.barra.setVisible(filtro_calidad_activo and total_seleccionadas > 0)

    def ejecutar(self, hito: HitoAtencion) -> None:
        cita_ids = self._selected_ids()
        if not cita_ids:
            return
        modo = self._resolver_modo()
        estado = estado_boton_hito_lote(modo, hito)
        if not estado.habilitado:
            self._on_fail("modo_programada_no_permitido")
            return
        if not self._confirmar(len(cita_ids)):
            return
        self._log_click(hito, modo, len(cita_ids))
        self._arrancar_worker(AccionLoteHitosDTO(cita_ids=cita_ids, hito=hito, modo_timestamp=modo))

    def _cargar_modos(self) -> None:
        self.combo_modo.blockSignals(True)
        self.combo_modo.clear()
        self.combo_modo.addItem(self._i18n.t("citas.hitos.lote.usar_ahora"), ModoTimestampHito.AHORA.value)
        self.combo_modo.addItem(
            self._i18n.t("citas.hitos.lote.usar_hora_programada"), ModoTimestampHito.PROGRAMADA.value
        )
        self.combo_modo.blockSignals(False)

    def _confirmar(self, total: int) -> bool:
        return (
            QMessageBox.question(
                self._parent,
                self._i18n.t("citas.hitos.lote.confirmar_titulo"),
                self._i18n.t("citas.hitos.lote.confirmar_texto").format(total=total),
            )
            == QMessageBox.Yes
        )

    def _resolver_modo(self) -> ModoTimestampHito:
        return ModoTimestampHito(self.combo_modo.currentData())

    def _actualizar_estado_botones(self) -> None:
        modo = self._resolver_modo()
        self._aplicar_estado(self.btn_llegada, estado_boton_hito_lote(modo, HitoAtencion.CHECK_IN))
        self._aplicar_estado(self.btn_inicio, estado_boton_hito_lote(modo, HitoAtencion.INICIO_CONSULTA))
        self._aplicar_estado(self.btn_fin, estado_boton_hito_lote(modo, HitoAtencion.FIN_CONSULTA))
        self._aplicar_estado(self.btn_salida, estado_boton_hito_lote(modo, HitoAtencion.CHECK_OUT))

    def _aplicar_estado(self, boton: QPushButton, estado) -> None:
        boton.setEnabled(estado.habilitado)
        boton.setToolTip(self._i18n.t(estado.tooltip_key) if estado.tooltip_key else "")

    def _arrancar_worker(self, accion: AccionLoteHitosDTO) -> None:
        self._thread = QThread(self._parent)
        self._worker = WorkerHitosLote(self._db_path, accion)
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

    def _on_started(self) -> None:
        for boton in (self.btn_llegada, self.btn_inicio, self.btn_fin, self.btn_salida):
            boton.setEnabled(False)
        self.combo_modo.setEnabled(False)
        self.lbl_estado.setText(self._i18n.t("citas.hitos.lote.guardando"))

    def _on_ok(self, dto: ResultadoLoteHitosDTO) -> None:
        self.combo_modo.setEnabled(True)
        self._actualizar_estado_botones()
        self.lbl_estado.setText("")
        texto = construir_resumen_hitos_lote(dto, self._i18n.t)
        LOGGER.info(
            "citas_hitos_lote_ok",
            extra={
                "action": "citas_hitos_lote_ok",
                "aplicadas": dto.aplicadas,
                "ya_estaban": dto.ya_estaban,
                "omitidas": dto.omitidas_por_orden + dto.no_encontradas,
                "errores": dto.errores,
            },
        )
        QMessageBox.information(self._parent, self._i18n.t("citas.tabs.lista"), texto)

    def _on_fail(self, reason_code: str) -> None:
        self.combo_modo.setEnabled(True)
        self._actualizar_estado_botones()
        self.lbl_estado.setText("")
        LOGGER.warning(
            "citas_hitos_lote_fail",
            extra={"action": "citas_hitos_lote_fail", "reason_code": reason_code},
        )
        QMessageBox.warning(self._parent, self._i18n.t("citas.tabs.lista"), self._i18n.t(reason_code))

    def _log_click(self, hito: HitoAtencion, modo: ModoTimestampHito, total: int) -> None:
        LOGGER.info(
            "citas_hitos_lote_click",
            extra={
                "action": "citas_hitos_lote_click",
                "hito": hito.value,
                "modo": modo.value,
                "total": total,
            },
        )
