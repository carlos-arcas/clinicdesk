from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDateEdit,
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
from clinicdesk.app.queries.confirmaciones_queries import ConfirmacionesQueries

_PAGE_SIZE = 20


class PageConfirmaciones(QWidget):
    def __init__(self, container: AppContainer, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._container = container
        self._i18n = i18n
        self._offset = 0
        self._total = 0
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
        for w in (self.cmb_rango, self.desde, self.hasta, self.cmb_riesgo, self.cmb_recordatorio, self.txt_buscar, self.btn_actualizar):
            filters.addWidget(w)
        root.addLayout(filters)

        self.table = QTableWidget(0, 8)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table)

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
        self._set_filter_options()
        self.table.setHorizontalHeaderLabels([
            t("confirmaciones.col.fecha"),
            t("confirmaciones.col.hora"),
            t("confirmaciones.col.paciente"),
            t("confirmaciones.col.medico"),
            t("confirmaciones.col.estado"),
            t("confirmaciones.col.riesgo"),
            t("confirmaciones.col.recordatorio"),
            t("confirmaciones.col.acciones"),
        ])

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
        custom = mode == "CUSTOM"
        self.desde.setEnabled(custom)
        self.hasta.setEnabled(custom)

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
        try:
            result = self._uc.ejecutar(self._build_filtros(), PaginacionConfirmacionesDTO(limit=_PAGE_SIZE, offset=self._offset))
        except Exception:
            self._show_error()
            return
        self._total = result.total
        self._render_banner(result.salud_prediccion.estado if result.salud_prediccion else "ROJO")
        self._render_rows(result.items)
        self.lbl_totales.setText(
            self._i18n.t("confirmaciones.paginacion.mostrando").format(mostrados=result.mostrados, total=result.total)
        )

    def _render_rows(self, rows) -> None:
        self.table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            inicio = item.inicio
            self.table.setItem(row, 0, QTableWidgetItem(inicio[:10]))
            self.table.setItem(row, 1, QTableWidgetItem(inicio[11:16]))
            self.table.setItem(row, 2, QTableWidgetItem(item.paciente))
            self.table.setItem(row, 3, QTableWidgetItem(item.medico))
            self.table.setItem(row, 4, QTableWidgetItem(item.estado_cita))
            self.table.setItem(row, 5, QTableWidgetItem(self._i18n.t(f"confirmaciones.riesgo.{item.riesgo.lower()}")))
            self.table.setItem(row, 6, QTableWidgetItem(self._i18n.t(f"confirmaciones.recordatorio.{item.recordatorio_estado.lower()}")))
            actions = QWidget(self.table)
            lay = QHBoxLayout(actions)
            lay.setContentsMargins(0, 0, 0, 0)
            btn_riesgo = QPushButton(self._i18n.t("confirmaciones.accion.ver_riesgo"), actions)
            btn_recordatorio = QPushButton(self._i18n.t("confirmaciones.accion.preparar_recordatorio"), actions)
            btn_riesgo.clicked.connect(lambda _=False, cita_id=item.cita_id: self._abrir_riesgo(cita_id))
            btn_recordatorio.clicked.connect(lambda _=False, cita_id=item.cita_id: self._abrir_recordatorio(cita_id))
            lay.addWidget(btn_riesgo)
            lay.addWidget(btn_recordatorio)
            self.table.setCellWidget(row, 7, actions)

    def _render_banner(self, estado: str) -> None:
        key = f"confirmaciones.prediccion.{estado.lower()}"
        self.banner.setText(self._i18n.t(key))
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
