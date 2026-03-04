from __future__ import annotations

import logging
from datetime import date, timedelta

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.confirmaciones import (
    FiltrosConfirmacionesDTO,
    PaginacionConfirmacionesDTO,
)
from clinicdesk.app.application.citas.filtros import redactar_texto_busqueda
from clinicdesk.app.application.prediccion_ausencias.aviso_salud_prediccion import (
    debe_mostrar_aviso_salud_prediccion,
)
from clinicdesk.app.container import AppContainer
from clinicdesk.app.application.usecases.registrar_telemetria import RegistrarTelemetria
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.riesgo_ausencia_dialog import RiesgoAusenciaDialog
from clinicdesk.app.pages.confirmaciones.columnas import claves_columnas_confirmaciones
from clinicdesk.app.pages.confirmaciones.lote_controller import GestorLoteConfirmaciones
from clinicdesk.app.pages.confirmaciones.lote_worker import AccionLoteDTO, WorkerRecordatoriosLote
from clinicdesk.app.pages.confirmaciones.acciones_whatsapp_rapido import estado_accion_whatsapp_rapida
from clinicdesk.app.pages.confirmaciones.tabla_actions import crear_actions_confirmacion
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget
from clinicdesk.app.ui.workers.listado_async_workers import CargaConfirmacionesWorker
from clinicdesk.app.infrastructure.sqlite.db_path import resolver_db_path_desde_conexion

_PAGE_SIZE = 20
_COL_CHECK = 0
LOGGER = logging.getLogger(__name__)


class PageConfirmaciones(QWidget):
    def __init__(self, container: AppContainer, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._container = container
        self._i18n = i18n
        self._offset = 0
        self._total = 0
        self._citas_seleccionadas: set[int] = set()
        self._cita_en_preparacion: int | None = None
        self._uc_telemetria = RegistrarTelemetria(container.telemetria_eventos_repo)
        self._thread_rapido: QThread | None = None
        self._worker_rapido: WorkerRecordatoriosLote | None = None
        self._thread_carga: QThread | None = None
        self._worker_carga: CargaConfirmacionesWorker | None = None
        self._token_carga = 0
        self._db_path = resolver_db_path_desde_conexion(container.connection)
        self._build_ui()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()

    def on_show(self) -> None:
        self._load_data(reset=True)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        self.lbl_title = QLabel()
        root.addWidget(self.lbl_title)
        self.banner = QLabel()
        self.btn_ir_prediccion = QPushButton()
        self.btn_ir_prediccion.clicked.connect(self._ir_a_prediccion)
        banner_row = QHBoxLayout()
        banner_row.addWidget(self.banner, 1)
        banner_row.addWidget(self.btn_ir_prediccion)
        root.addLayout(banner_row)

        filters = QHBoxLayout()
        self.cmb_rango = QComboBox()
        self.desde = QDateEdit()
        self.hasta = QDateEdit()
        self.cmb_riesgo = QComboBox()
        self.cmb_recordatorio = QComboBox()
        self.txt_buscar = QLineEdit()
        self.btn_actualizar = QPushButton()
        self.btn_actualizar.clicked.connect(lambda: self._load_data(reset=True))
        self.cmb_rango.currentIndexChanged.connect(self._on_rango_changed)
        widgets_filtro = (
            self.cmb_rango,
            self.desde,
            self.hasta,
            self.cmb_riesgo,
            self.cmb_recordatorio,
            self.txt_buscar,
            self.btn_actualizar,
        )
        for widget in widgets_filtro:
            filters.addWidget(widget)
        root.addLayout(filters)

        seleccion_row = QHBoxLayout()
        self.chk_todo_visible = QCheckBox()
        self.chk_todo_visible.stateChanged.connect(self._toggle_todo_visible)
        self.lbl_seleccionadas = QLabel()
        seleccion_row.addWidget(self.chk_todo_visible)
        seleccion_row.addWidget(self.lbl_seleccionadas)
        seleccion_row.addStretch(1)
        root.addLayout(seleccion_row)

        self.table = QTableWidget(0, 9)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemChanged.connect(self._on_item_changed)

        self._lote = GestorLoteConfirmaciones(
            self,
            self._i18n,
            self._container.recordatorios_citas_facade,
            selected_ids=lambda: tuple(sorted(self._citas_seleccionadas)),
            on_done=lambda: self._load_data(reset=False),
        )
        footer = QHBoxLayout()
        self.lbl_totales = QLabel()
        self.btn_prev = QPushButton()
        self.btn_next = QPushButton()
        self.btn_prev.clicked.connect(self._prev)
        self.btn_next.clicked.connect(self._next)
        footer.addWidget(self.lbl_totales)
        footer.addStretch(1)
        footer.addWidget(self.btn_prev)
        footer.addWidget(self.btn_next)
        contenido = QWidget(self)
        contenido_layout = QVBoxLayout(contenido)
        contenido_layout.setContentsMargins(0, 0, 0, 0)
        contenido_layout.addWidget(self.table)
        contenido_layout.addWidget(self._lote.barra)
        contenido_layout.addLayout(footer)

        self._estado_pantalla = EstadoPantallaWidget(self._i18n, self)
        self._estado_pantalla.set_content(contenido)
        root.addWidget(self._estado_pantalla)

    def _retranslate(self) -> None:
        t = self._i18n.t
        self.lbl_title.setText(t("confirmaciones.titulo"))
        self.btn_ir_prediccion.setText(t("prediccion_ausencias.ir_a_prediccion"))
        self.btn_actualizar.setText(t("confirmaciones.filtro.actualizar"))
        self.btn_prev.setText(t("confirmaciones.paginacion.anterior"))
        self.btn_next.setText(t("confirmaciones.paginacion.siguiente"))
        self.txt_buscar.setPlaceholderText(t("confirmaciones.filtro.buscar"))
        self.chk_todo_visible.setText(t("confirmaciones.seleccion.todo_visible"))
        self._lote.retranslate()
        self._set_filter_options()
        self.table.setHorizontalHeaderLabels(self._labels_columnas())
        self._actualizar_estado_seleccion()

    def _labels_columnas(self) -> list[str]:
        mapa = {
            "seleccion": self._i18n.t("confirmaciones.seleccion.seleccionar"),
            "fecha": self._i18n.t("confirmaciones.col.fecha"),
            "hora": self._i18n.t("confirmaciones.col.hora"),
            "paciente": self._i18n.t("confirmaciones.col.paciente"),
            "medico": self._i18n.t("confirmaciones.col.medico"),
            "estado": self._i18n.t("confirmaciones.col.estado"),
            "riesgo": self._i18n.t("confirmaciones.col.riesgo"),
            "recordatorio": self._i18n.t("confirmaciones.col.recordatorio"),
            "acciones": self._i18n.t("confirmaciones.col.acciones"),
        }
        return [mapa[clave] for clave in claves_columnas_confirmaciones()]

    def _set_filter_options(self) -> None:
        t = self._i18n.t
        self.cmb_rango.clear()
        self.cmb_rango.addItem(t("confirmaciones.filtro.rango.hoy"), "HOY")
        self.cmb_rango.addItem(t("confirmaciones.filtro.rango.7d"), "7D")
        self.cmb_rango.addItem(t("confirmaciones.filtro.rango.30d"), "30D")
        self.cmb_rango.addItem(t("confirmaciones.filtro.rango.custom"), "CUSTOM")
        self.cmb_riesgo.clear()
        self.cmb_riesgo.addItem(t("confirmaciones.filtro.riesgo.todos"), "TODOS")
        self.cmb_riesgo.addItem(t("confirmaciones.filtro.riesgo.alto_medio"), "ALTO_MEDIO")
        self.cmb_riesgo.addItem(t("confirmaciones.filtro.riesgo.solo_alto"), "SOLO_ALTO")
        self.cmb_recordatorio.clear()
        self.cmb_recordatorio.addItem(t("confirmaciones.filtro.recordatorio.todos"), "TODOS")
        self.cmb_recordatorio.addItem(t("confirmaciones.filtro.recordatorio.sin_preparar"), "SIN_PREPARAR")
        self.cmb_recordatorio.addItem(t("confirmaciones.filtro.recordatorio.no_enviado"), "NO_ENVIADO")
        self._on_rango_changed()

    def _on_rango_changed(self) -> None:
        mode = self.cmb_rango.currentData()
        today = date.today()
        end = today + timedelta(days=7)
        if mode == "HOY":
            end = today
        elif mode == "30D":
            end = today + timedelta(days=30)
        self.desde.setDate(today if mode != "CUSTOM" else self.desde.date())
        self.hasta.setDate(end if mode != "CUSTOM" else self.hasta.date())
        self.desde.setEnabled(mode == "CUSTOM")
        self.hasta.setEnabled(mode == "CUSTOM")

    def _build_filtros(self) -> FiltrosConfirmacionesDTO:
        return FiltrosConfirmacionesDTO(
            desde=self.desde.date().toString("yyyy-MM-dd"),
            hasta=self.hasta.date().toString("yyyy-MM-dd"),
            texto_paciente=self.txt_buscar.text(),
            recordatorio_filtro=str(self.cmb_recordatorio.currentData()),
            riesgo_filtro=str(self.cmb_riesgo.currentData()),
        )

    def _load_data(self, *, reset: bool) -> None:
        self._token_carga += 1
        token = self._token_carga
        if reset:
            self._offset = 0
        self._log_carga(reset)
        self._limpiar_seleccion()
        self._estado_pantalla.set_loading("ux_states.confirmaciones.loading")
        self._arrancar_worker_carga(token=token)

    def _arrancar_worker_carga(self, *, token: int) -> None:
        if self._thread_carga is not None and self._thread_carga.isRunning():
            return
        self._thread_carga = QThread(self)
        self._worker_carga = CargaConfirmacionesWorker(
            db_path=self._db_path,
            filtros=self._build_filtros(),
            paginacion=PaginacionConfirmacionesDTO(limit=_PAGE_SIZE, offset=self._offset),
            riesgo_uc=self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc,
            salud_uc=self._container.prediccion_ausencias_facade.obtener_salud_uc,
        )
        self._worker_carga.moveToThread(self._thread_carga)
        self._thread_carga.started.connect(self._worker_carga.run)
        self._worker_carga.finished_ok.connect(lambda result: self._on_carga_ok(result, token))
        self._worker_carga.finished_error.connect(lambda error: self._on_carga_error(error, token))
        self._worker_carga.finished.connect(self._thread_carga.quit)
        self._worker_carga.finished.connect(self._worker_carga.deleteLater)
        self._thread_carga.finished.connect(self._thread_carga.deleteLater)
        self._thread_carga.finished.connect(self._reset_worker_carga)
        self._thread_carga.start()

    def _reset_worker_carga(self) -> None:
        self._thread_carga = None
        self._worker_carga = None

    def _on_carga_ok(self, result, token: int) -> None:
        if token != self._token_carga:
            return
        self._total = result.total
        self._render_banner(result.salud_prediccion.estado if result.salud_prediccion else "ROJO")
        self._render_rows(result.items)
        self.lbl_totales.setText(
            self._i18n.t("confirmaciones.paginacion.mostrando").format(mostrados=result.mostrados, total=result.total)
        )
        if not result.items:
            self._estado_pantalla.set_empty(
                "ux_states.confirmaciones.empty",
                cta_text_key="ux_states.confirmaciones.cta_refresh",
                on_cta=lambda: self._load_data(reset=True),
            )
            return
        self._estado_pantalla.set_content(self.table.parentWidget())

    def _on_carga_error(self, error_type: str, token: int) -> None:
        if token != self._token_carga:
            return
        LOGGER.warning(
            "confirmaciones_carga_error",
            extra={"action": "confirmaciones_carga_error", "error": error_type},
        )
        self._estado_pantalla.set_error(
            "ux_states.confirmaciones.error",
            detalle_tecnico=error_type,
            on_retry=lambda: self._load_data(reset=False),
        )

    def _log_carga(self, reset: bool) -> None:
        LOGGER.info(
            "confirmaciones_carga",
            extra={
                "action": "confirmaciones_carga",
                "reset": reset,
                "offset": self._offset,
                "texto_redactado": redactar_texto_busqueda(self.txt_buscar.text()),
                "riesgo_filtro": str(self.cmb_riesgo.currentData()),
                "recordatorio_filtro": str(self.cmb_recordatorio.currentData()),
            },
        )

    def _render_rows(self, rows) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            self._render_row(row, item)
        self.table.blockSignals(False)
        self._actualizar_estado_seleccion()

    def _render_row(self, row: int, item) -> None:
        selector = QTableWidgetItem()
        selector.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        selector.setCheckState(Qt.Checked if item.cita_id in self._citas_seleccionadas else Qt.Unchecked)
        selector.setData(Qt.UserRole, item.cita_id)
        self.table.setItem(row, 0, selector)
        inicio = item.inicio
        self.table.setItem(row, 1, QTableWidgetItem(inicio[:10]))
        self.table.setItem(row, 2, QTableWidgetItem(inicio[11:16]))
        self.table.setItem(row, 3, QTableWidgetItem(item.paciente))
        self.table.setItem(row, 4, QTableWidgetItem(item.medico))
        self.table.setItem(row, 5, QTableWidgetItem(item.estado_cita))
        self.table.setItem(row, 6, QTableWidgetItem(self._i18n.t(f"confirmaciones.riesgo.{item.riesgo.lower()}")))
        self.table.setItem(
            row, 7, QTableWidgetItem(self._i18n.t(f"confirmaciones.recordatorio.{item.recordatorio_estado.lower()}"))
        )
        self.table.setCellWidget(row, 8, self._crear_actions(item))

    def _crear_actions(self, item) -> QWidget:
        estado = estado_accion_whatsapp_rapida(item.riesgo, item.recordatorio_estado, item.tiene_telefono)
        tooltip = self._i18n.t(estado.tooltip_key) if estado.tooltip_key else ""
        return crear_actions_confirmacion(
            self.table,
            self._i18n.t("confirmaciones.accion.ver_riesgo"),
            self._i18n.t("confirmaciones.accion.preparar_whatsapp_rapido"),
            self._i18n.t("confirmaciones.accion.preparando_fila"),
            estado,
            self._cita_en_preparacion == item.cita_id,
            tooltip,
            lambda: self._abrir_riesgo(item.cita_id),
            lambda: self._preparar_whatsapp_rapido(item),
        )

    def _toggle_todo_visible(self, state: int) -> None:
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, _COL_CHECK)
            if item is not None:
                item.setCheckState(check_state)
                self._actualizar_cita_seleccionada(item)
        self.table.blockSignals(False)
        self._actualizar_estado_seleccion()

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != _COL_CHECK:
            return
        self._actualizar_cita_seleccionada(item)
        self._actualizar_estado_seleccion()

    def _actualizar_cita_seleccionada(self, item: QTableWidgetItem) -> None:
        cita_id = item.data(Qt.UserRole)
        if not isinstance(cita_id, int):
            return
        if item.checkState() == Qt.Checked:
            self._citas_seleccionadas.add(cita_id)
            return
        self._citas_seleccionadas.discard(cita_id)

    def _actualizar_estado_seleccion(self) -> None:
        total = len(self._citas_seleccionadas)
        self.lbl_seleccionadas.setText(self._i18n.t("confirmaciones.seleccion.contador").format(total=total))
        self._lote.actualizar_visibilidad(total)

    def _limpiar_seleccion(self) -> None:
        self._citas_seleccionadas.clear()
        self.chk_todo_visible.setCheckState(Qt.Unchecked)
        self._actualizar_estado_seleccion()

    def _render_banner(self, estado: str) -> None:
        mostrar = debe_mostrar_aviso_salud_prediccion(self._riesgo_activado(), estado)
        self.banner.setText(self._i18n.t("prediccion_ausencias.aviso_salud_prediccion") if mostrar else "")
        self.banner.setVisible(mostrar)
        self.btn_ir_prediccion.setVisible(mostrar)
        if mostrar:
            LOGGER.info(
                "aviso_salud_prediccion_mostrar",
                extra={"action": "aviso_salud_prediccion_mostrar", "page": "confirmaciones", "estado": estado},
            )

    @staticmethod
    def _riesgo_activado() -> bool:
        return True

    def _abrir_riesgo(self, cita_id: int) -> None:
        explicacion = self._container.prediccion_ausencias_facade.obtener_explicacion_riesgo_uc.ejecutar(cita_id)
        salud = self._container.prediccion_ausencias_facade.obtener_salud_uc.ejecutar()
        dialog = RiesgoAusenciaDialog(self._i18n, explicacion, salud, self)
        dialog.exec()
        self._registrar_telemetria("explicacion_ver_por_que", "ok", cita_id)

    def _preparar_whatsapp_rapido(self, item) -> None:
        if self._cita_en_preparacion is not None:
            return
        self._cita_en_preparacion = item.cita_id
        self._load_data(reset=False)
        self._log_whatsapp_rapido_click(item)
        self._registrar_telemetria("confirmaciones_whatsapp_rapido", "click", item.cita_id)
        self._arrancar_worker_rapido(item.cita_id)

    def _arrancar_worker_rapido(self, cita_id: int) -> None:
        self._thread_rapido = QThread(self)
        accion = AccionLoteDTO(tipo="PREPARAR", cita_ids=(cita_id,), canal="WHATSAPP")
        self._worker_rapido = WorkerRecordatoriosLote(self._container.recordatorios_citas_facade, accion)
        self._worker_rapido.moveToThread(self._thread_rapido)
        self._thread_rapido.started.connect(self._worker_rapido.run)
        self._worker_rapido.finished_ok.connect(self._on_whatsapp_rapido_ok)
        self._worker_rapido.finished_error.connect(self._on_whatsapp_rapido_fail)
        self._worker_rapido.finished.connect(self._thread_rapido.quit)
        self._worker_rapido.finished.connect(self._worker_rapido.deleteLater)
        self._thread_rapido.finished.connect(self._thread_rapido.deleteLater)
        self._thread_rapido.start()

    def _on_whatsapp_rapido_ok(self, _dto) -> None:
        LOGGER.info(
            "confirmaciones_whatsapp_rapido_ok",
            extra={"action": "confirmaciones_whatsapp_rapido_ok", "reason_code": "ok"},
        )
        self._registrar_telemetria("confirmaciones_whatsapp_rapido", "ok", self._cita_en_preparacion)
        self._cita_en_preparacion = None
        self._load_data(reset=False)
        QMessageBox.information(
            self, self._i18n.t("confirmaciones.titulo"), self._i18n.t("confirmaciones.accion.hecho")
        )

    def _on_whatsapp_rapido_fail(self, reason_code: str) -> None:
        LOGGER.warning(
            "confirmaciones_whatsapp_rapido_fail",
            extra={"action": "confirmaciones_whatsapp_rapido_fail", "reason_code": reason_code},
        )
        self._registrar_telemetria("confirmaciones_whatsapp_rapido", "fail", self._cita_en_preparacion)
        self._cita_en_preparacion = None
        self._load_data(reset=False)
        QMessageBox.warning(
            self, self._i18n.t("confirmaciones.titulo"), self._i18n.t("confirmaciones.accion.error_guardar")
        )

    def _log_whatsapp_rapido_click(self, item) -> None:
        LOGGER.info(
            "confirmaciones_whatsapp_rapido_click",
            extra={
                "action": "confirmaciones_whatsapp_rapido_click",
                "cita_id": item.cita_id,
                "riesgo": item.riesgo,
                "estado_recordatorio": item.recordatorio_estado,
            },
        )

    def _registrar_telemetria(self, evento: str, resultado: str, cita_id: int | None) -> None:
        try:
            self._uc_telemetria.ejecutar(
                contexto_usuario=self._container.user_context,
                evento=evento,
                contexto=f"page=confirmaciones;resultado={resultado}",
                entidad_tipo="cita",
                entidad_id=cita_id,
            )
        except Exception:
            return

    def _prev(self) -> None:
        self._offset = max(0, self._offset - _PAGE_SIZE)
        self._load_data(reset=False)

    def _next(self) -> None:
        if self._offset + _PAGE_SIZE >= self._total:
            return
        self._offset += _PAGE_SIZE
        self._load_data(reset=False)

    def _ir_a_prediccion(self) -> None:
        LOGGER.info(
            "aviso_salud_prediccion_cta",
            extra={"action": "aviso_salud_prediccion_cta", "page": "confirmaciones", "destino": "prediccion"},
        )
        window = self.window()
        if hasattr(window, "navigate"):
            window.navigate("prediccion_ausencias")
