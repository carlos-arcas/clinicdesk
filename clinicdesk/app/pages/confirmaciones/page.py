from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt
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
    ObtenerConfirmacionesCitas,
    PaginacionConfirmacionesDTO,
)
from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.recordatorio_cita_dialog import RecordatorioCitaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_dialog import RiesgoAusenciaDialog
from clinicdesk.app.pages.confirmaciones.lote_controller import GestorLoteConfirmaciones
from clinicdesk.app.pages.confirmaciones.tabla_actions import crear_actions_confirmacion
from clinicdesk.app.queries.confirmaciones_queries import ConfirmacionesQueries

_PAGE_SIZE = 20
_COL_CHECK = 0


class PageConfirmaciones(QWidget):
    def __init__(self, container: AppContainer, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._container = container
        self._i18n = i18n
        self._offset = 0
        self._total = 0
        self._citas_seleccionadas: set[int] = set()
        self._uc = ObtenerConfirmacionesCitas(
            queries=ConfirmacionesQueries(container.connection),
            obtener_riesgo_uc=container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc,
            obtener_salud_uc=container.prediccion_ausencias_facade.obtener_salud_uc,
        )
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
        root.addWidget(self.table)

        self._lote = GestorLoteConfirmaciones(
            self,
            self._i18n,
            self._container.recordatorios_citas_facade,
            selected_ids=lambda: tuple(sorted(self._citas_seleccionadas)),
            on_done=lambda: self._load_data(reset=False),
        )
        root.addWidget(self._lote.barra)

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
        root.addLayout(footer)
    def _retranslate(self) -> None:
        t = self._i18n.t
        self.lbl_title.setText(t("confirmaciones.titulo"))
        self.btn_ir_prediccion.setText(t("confirmaciones.accion.ir_prediccion"))
        self.btn_actualizar.setText(t("confirmaciones.filtro.actualizar"))
        self.btn_prev.setText(t("confirmaciones.paginacion.anterior"))
        self.btn_next.setText(t("confirmaciones.paginacion.siguiente"))
        self.txt_buscar.setPlaceholderText(t("confirmaciones.filtro.buscar"))
        self.chk_todo_visible.setText(t("confirmaciones.seleccion.todo_visible"))
        self._lote.retranslate()
        self._set_filter_options()
        self.table.setHorizontalHeaderLabels(
            [
                t("confirmaciones.seleccion.seleccionar"),
                t("confirmaciones.col.fecha"),
                t("confirmaciones.col.hora"),
                t("confirmaciones.col.paciente"),
                t("confirmaciones.col.medico"),
                t("confirmaciones.col.estado"),
                t("confirmaciones.col.riesgo"),
                t("confirmaciones.col.recordatorio"),
                t("confirmaciones.col.acciones"),
            ]
        )
        self._actualizar_estado_seleccion()
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
        if reset:
            self._offset = 0
        self._limpiar_seleccion()
        try:
            result = self._uc.ejecutar(self._build_filtros(), PaginacionConfirmacionesDTO(limit=_PAGE_SIZE, offset=self._offset))
        except Exception:
            self._show_error()
            return
        self._total = result.total
        self._render_banner(result.salud_prediccion.estado if result.salud_prediccion else "ROJO")
        self._render_rows(result.items)
        self.lbl_totales.setText(self._i18n.t("confirmaciones.paginacion.mostrando").format(mostrados=result.mostrados, total=result.total))
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
        self.table.setItem(row, 7, QTableWidgetItem(self._i18n.t(f"confirmaciones.recordatorio.{item.recordatorio_estado.lower()}")))
        self.table.setCellWidget(row, 8, self._crear_actions(item.cita_id))
    def _crear_actions(self, cita_id: int) -> QWidget:
        return crear_actions_confirmacion(
            self.table,
            self._i18n.t("confirmaciones.accion.ver_riesgo"),
            self._i18n.t("confirmaciones.accion.preparar_recordatorio"),
            lambda: self._abrir_riesgo(cita_id),
            lambda: self._abrir_recordatorio(cita_id),
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
        self.banner.setText(self._i18n.t(f"confirmaciones.prediccion.{estado.lower()}"))
        self.btn_ir_prediccion.setVisible(estado != "VERDE")
    def _show_error(self) -> None:
        msg = QMessageBox(self)
        msg.setText(self._i18n.t("confirmaciones.error.carga"))
        msg.setStandardButtons(QMessageBox.Retry)
        msg.button(QMessageBox.Retry).setText(self._i18n.t("confirmaciones.error.reintentar"))
        msg.exec()
    def _abrir_riesgo(self, cita_id: int) -> None:
        explicacion = self._container.prediccion_ausencias_facade.obtener_explicacion_riesgo_uc.ejecutar(cita_id)
        salud = self._container.prediccion_ausencias_facade.obtener_salud_uc.ejecutar()
        dialog = RiesgoAusenciaDialog(self._i18n, explicacion, salud, self)
        dialog.exec()
    def _abrir_recordatorio(self, cita_id: int) -> None:
        dialog = RecordatorioCitaDialog(self._container, self._i18n, cita_id, self)
        dialog.exec()
    def _prev(self) -> None:
        self._offset = max(0, self._offset - _PAGE_SIZE)
        self._load_data(reset=False)
    def _next(self) -> None:
        if self._offset + _PAGE_SIZE >= self._total:
            return
        self._offset += _PAGE_SIZE
        self._load_data(reset=False)
    def _ir_a_prediccion(self) -> None:
        window = self.window()
        if hasattr(window, "navigate"):
            window.navigate("prediccion_ausencias")
