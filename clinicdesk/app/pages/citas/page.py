from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.citas import (
    ATRIBUTOS_CITA,
    BuscarCitasParaCalendario,
    BuscarCitasParaLista,
    FiltrosCitasDTO,
    PaginacionCitasDTO,
    formatear_valor_atributo_cita,
    normalizar_filtros_citas,
    sanear_columnas_citas,
)
from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import RIESGO_NO_DISPONIBLE
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.container import AppContainer
from clinicdesk.app.controllers.citas_controller import CitasController
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.recordatorio_cita_dialog import RecordatorioCitaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_dialog import RiesgoAusenciaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_ui import (
    SETTINGS_KEY_RIESGO_AGENDA,
    construir_dtos_desde_calendario,
    resolver_texto_riesgo,
)
from clinicdesk.app.pages.citas.widgets.dialogo_selector_columnas_citas import DialogoSelectorColumnasCitas
from clinicdesk.app.pages.citas.widgets.panel_filtros_citas_widget import PanelFiltrosCitasWidget
from clinicdesk.app.pages.citas.widgets.persistencia_citas_settings import (
    EstadoPersistidoFiltrosCitas,
    clave_columnas_citas,
    claves_filtros_citas,
    deserializar_columnas_citas,
    deserializar_filtros_citas,
    estado_restauracion_columnas,
    serializar_columnas_citas,
    serializar_filtros_citas,
)
from clinicdesk.app.pages.citas.widgets.tooltip_citas import CLAVES_TOOLTIP_POR_DEFECTO, construir_tooltip_cita
from clinicdesk.app.queries.citas_queries import CitaRow, CitasQueries

LOGGER = get_logger(__name__)


class PageCitas(QWidget):
    def __init__(self, container: AppContainer, i18n: I18nManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._i18n = i18n
        self._queries = CitasQueries(container)
        self._buscar_lista_uc = BuscarCitasParaLista(self._queries)
        self._buscar_calendario_uc = BuscarCitasParaCalendario(self._queries)
        self._controller = CitasController(self, container)
        self._can_write = container.user_context.can_write
        self._settings = QSettings("clinicdesk", "ui")
        self._filtros_aplicados = FiltrosCitasDTO()
        self._columnas_lista: tuple[str, ...] = tuple()
        self._citas_lista_ids: list[int] = []
        self._riesgo_enabled = False

        self._build_ui()
        self._bind_events()
        self._restaurar_estado_ui()
        self._refresh_calendario()
        self._programar_refresco_lista()

    def _build_ui(self) -> None:
        self.tabs = QTabWidget(self)
        self.calendar = QCalendarWidget()
        self.lbl_date = QLabel(self)
        self.btn_new = QPushButton(self._i18n.t("citas.acciones.nueva"))
        self.btn_delete = QPushButton(self._i18n.t("citas.acciones.eliminar"))
        self.btn_new.setEnabled(self._can_write)
        self.btn_delete.setEnabled(False)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "", "", "", "", "", "", ""])
        self.table.setColumnHidden(0, True)

        tab_calendario = QWidget(self)
        izq = QVBoxLayout()
        izq.addWidget(self.calendar)
        izq.addWidget(self.lbl_date)
        izq.addWidget(self.btn_new)
        izq.addWidget(self.btn_delete)
        der = QVBoxLayout()
        der.addWidget(self.table)
        lay_cal = QHBoxLayout(tab_calendario)
        lay_cal.addLayout(izq, 1)
        lay_cal.addLayout(der, 3)

        tab_lista = QWidget(self)
        self.panel_filtros = PanelFiltrosCitasWidget(self._i18n, tab_lista)
        self.btn_columnas = QPushButton(self._i18n.t("citas.lista.columnas.boton"), tab_lista)
        self.lbl_estado = QLabel("", tab_lista)
        self.btn_reintentar = QPushButton(self._i18n.t("citas.ux.reintentar"), tab_lista)
        self.btn_reintentar.setVisible(False)
        self.lbl_aviso_columnas = QLabel("", tab_lista)
        self.table_lista = QTableWidget(0, 0, tab_lista)
        self.table_lista.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_lista.setContextMenuPolicy(Qt.CustomContextMenu)

        barra = QHBoxLayout()
        barra.addWidget(self.btn_columnas)
        barra.addStretch(1)
        barra.addWidget(self.lbl_estado)
        barra.addWidget(self.btn_reintentar)

        layout_lista = QVBoxLayout(tab_lista)
        layout_lista.addWidget(self.panel_filtros)
        layout_lista.addLayout(barra)
        layout_lista.addWidget(self.lbl_aviso_columnas)
        layout_lista.addWidget(self.table_lista)

        self.tabs.addTab(tab_calendario, self._i18n.t("citas.tabs.calendario"))
        self.tabs.addTab(tab_lista, self._i18n.t("citas.tabs.lista"))
        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

    def _bind_events(self) -> None:
        self.calendar.selectionChanged.connect(self._refresh_calendario)
        self.btn_new.clicked.connect(self._on_new)
        self.btn_delete.clicked.connect(self._on_delete)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_calendario_item_double_clicked)
        self.table.customContextMenuRequested.connect(self._on_calendario_context_menu)
        self.panel_filtros.filtros_aplicados.connect(self._on_filtros_aplicados)
        self.btn_columnas.clicked.connect(self._abrir_selector_columnas)
        self.btn_reintentar.clicked.connect(self._programar_refresco_lista)
        self.table_lista.itemDoubleClicked.connect(self._on_lista_item_double_clicked)
        self.table_lista.customContextMenuRequested.connect(self._on_lista_context_menu)

    def on_show(self) -> None:
        self._riesgo_enabled = bool(int(self._settings.value(SETTINGS_KEY_RIESGO_AGENDA, 0)))
        self._refresh_calendario()
        self._programar_refresco_lista()

    def _restaurar_estado_ui(self) -> None:
        filtros = claves_filtros_citas()
        data = EstadoPersistidoFiltrosCitas(
            preset=str(self._settings.value(filtros["preset"], "HOY")),
            desde_iso=self._settings.value(filtros["desde"]),
            hasta_iso=self._settings.value(filtros["hasta"]),
            texto=self._settings.value(filtros["texto"]),
            estado=self._settings.value(filtros["estado"]),
            medico_id=self._settings.value(filtros["medico_id"]),
            sala_id=self._settings.value(filtros["sala_id"]),
            paciente_id=self._settings.value(filtros["paciente_id"]),
        )
        self._filtros_aplicados = deserializar_filtros_citas(data)
        self.panel_filtros.set_filtros(self._filtros_aplicados)
        saved = self._settings.value(clave_columnas_citas())
        self._columnas_lista = deserializar_columnas_citas(saved)
        if estado_restauracion_columnas(saved):
            self.lbl_aviso_columnas.setText(self._i18n.t("citas.lista.columnas.restauradas"))

    def _on_filtros_aplicados(self, filtros: object) -> None:
        if not isinstance(filtros, FiltrosCitasDTO):
            return
        self._filtros_aplicados = normalizar_filtros_citas(filtros, datetime.now())
        self._guardar_filtros()
        self._refresh_calendario()
        self._programar_refresco_lista()

    def _guardar_filtros(self) -> None:
        data = serializar_filtros_citas(self._filtros_aplicados)
        for clave, key in claves_filtros_citas().items():
            self._settings.setValue(key, getattr(data, f"{clave}_iso", None) if clave in {"desde", "hasta"} else getattr(data, clave))

    def _programar_refresco_lista(self) -> None:
        self._set_estado_lista("citas.ux.cargando", loading=True)
        QTimer.singleShot(0, self._refresh_lista)

    def _refresh_calendario(self) -> None:
        filtros = normalizar_filtros_citas(self._filtros_aplicados, datetime.now())
        self.lbl_date.setText(self._i18n.t("citas.calendario.fecha").format(fecha=self.calendar.selectedDate().toString("yyyy-MM-dd")))
        try:
            items = self._buscar_calendario_uc.ejecutar(filtros, CLAVES_TOOLTIP_POR_DEFECTO)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("citas_calendario_error", extra={"error": str(exc)})
            self.table.setRowCount(0)
            return
        riesgos = self._obtener_riesgo_citas_calendario([self._mapear_row_calendario(x) for x in items]) if self._riesgo_enabled else {}
        self.table.setRowCount(0)
        for item in items:
            item = dict(item)
            item["riesgo_ausencia"] = resolver_texto_riesgo(riesgos.get(int(item["cita_id"]), RIESGO_NO_DISPONIBLE), self._i18n).texto
            self._agregar_fila_calendario(item)

    def _refresh_lista(self) -> None:
        try:
            resultado = self._buscar_lista_uc.ejecutar(self._filtros_aplicados, self._columnas_lista, PaginacionCitasDTO(limit=500, offset=0))
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("citas_lista_error", extra={"error": str(exc)})
            self._set_estado_lista("citas.ux.error", error=True)
            return
        self._render_lista(resultado.items)
        if not resultado.items:
            self._set_estado_lista("citas.ux.vacio")
        else:
            self._set_estado_lista(None)

    def _render_lista(self, rows: list[dict[str, object]]) -> None:
        self.table_lista.setRowCount(0)
        columnas, _ = sanear_columnas_citas(self._columnas_lista)
        visibles = [c for c in columnas if c != "cita_id"]
        headers = {x.clave: self._i18n.t(x.i18n_key_cabecera) for x in ATRIBUTOS_CITA}
        self.table_lista.setColumnCount(len(visibles))
        self.table_lista.setHorizontalHeaderLabels([headers[c] for c in visibles])
        self._citas_lista_ids = [int(row["cita_id"]) for row in rows]
        for row in rows:
            idx = self.table_lista.rowCount()
            self.table_lista.insertRow(idx)
            for col, clave in enumerate(visibles):
                self.table_lista.setItem(idx, col, QTableWidgetItem(formatear_valor_atributo_cita(clave, row)))

    def _agregar_fila_calendario(self, item: dict[str, object]) -> None:
        idx = self.table.rowCount()
        self.table.insertRow(idx)
        valores = [
            str(item.get("cita_id", "")),
            formatear_valor_atributo_cita("fecha", item),
            formatear_valor_atributo_cita("hora_inicio", item),
            formatear_valor_atributo_cita("paciente", item),
            formatear_valor_atributo_cita("medico", item),
            formatear_valor_atributo_cita("sala", item),
            formatear_valor_atributo_cita("estado", item),
            formatear_valor_atributo_cita("incidencias", item),
        ]
        tooltip = construir_tooltip_cita(self._i18n, item)
        for col, valor in enumerate(valores):
            celda = QTableWidgetItem(valor)
            celda.setToolTip(tooltip)
            self.table.setItem(idx, col, celda)

    def _set_estado_lista(self, i18n_key: str | None, loading: bool = False, error: bool = False) -> None:
        self.lbl_estado.setText(self._i18n.t(i18n_key) if i18n_key else "")
        self.btn_reintentar.setVisible(error)
        self.btn_columnas.setEnabled(not loading)
        self.panel_filtros.setEnabled(not loading)

    def _abrir_selector_columnas(self) -> None:
        dialogo = DialogoSelectorColumnasCitas(self._i18n, self._columnas_lista, self)
        if dialogo.exec() != dialogo.Accepted:
            return
        self._columnas_lista = dialogo.columnas_seleccionadas()
        self._settings.setValue(clave_columnas_citas(), serializar_columnas_citas(self._columnas_lista))
        self._programar_refresco_lista()

    def _mapear_row_calendario(self, fila: dict[str, object]) -> CitaRow:
        return CitaRow(
            id=int(fila.get("cita_id", 0)),
            inicio=str(fila.get("inicio", "")),
            fin=str(fila.get("fin", "")),
            paciente_id=int(fila.get("paciente_id", 0)),
            paciente_nombre=str(fila.get("paciente", "")),
            medico_id=int(fila.get("medico_id", 0)),
            medico_nombre=str(fila.get("medico", "")),
            sala_id=int(fila.get("sala_id", 0)),
            sala_nombre=str(fila.get("sala", "")),
            estado=str(fila.get("estado", "")),
            motivo=None,
        )

    def _obtener_riesgo_citas_calendario(self, rows: list[CitaRow]) -> dict[int, str]:
        return self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc.ejecutar(construir_dtos_desde_calendario(rows, datetime.now()))

    def _on_lista_item_double_clicked(self, item: QTableWidgetItem) -> None:
        cita_id = self._cita_id_lista(item.row())
        if cita_id and self._riesgo_enabled:
            self._abrir_dialogo_riesgo(cita_id)

    def _on_calendario_item_double_clicked(self, item: QTableWidgetItem) -> None:
        if self._riesgo_enabled and (cita_id := self._cita_id_calendario(item.row())):
            self._abrir_dialogo_riesgo(cita_id)

    def _on_lista_context_menu(self, point) -> None:
        item = self.table_lista.itemAt(point)
        if item is None:
            return
        self._abrir_menu_cita(self._cita_id_lista(item.row()), self.table_lista.mapToGlobal(point))

    def _on_calendario_context_menu(self, point) -> None:
        item = self.table.itemAt(point)
        if item is None:
            return
        self._abrir_menu_cita(self._cita_id_calendario(item.row()), self.table.mapToGlobal(point))

    def _abrir_menu_cita(self, cita_id: int | None, global_point) -> None:
        if cita_id is None:
            return
        menu = QMenu(self)
        action_recordatorio = QAction(self._i18n.t("recordatorio.accion.preparar"), self)
        action_recordatorio.triggered.connect(lambda: self._abrir_dialogo_recordatorio(cita_id))
        menu.addAction(action_recordatorio)
        menu.exec(global_point)

    def _cita_id_lista(self, row: int) -> int | None:
        return self._citas_lista_ids[row] if 0 <= row < len(self._citas_lista_ids) else None

    def _cita_id_calendario(self, row: int) -> int | None:
        item = self.table.item(row, 0)
        return int(item.text()) if item and item.text().isdigit() else None

    def _selected_id(self) -> Optional[int]:
        return self._cita_id_calendario(self.table.currentRow())

    def _on_selection_changed(self) -> None:
        self.btn_delete.setEnabled(self._can_write and self._selected_id() is not None)

    def _on_new(self) -> None:
        if self._can_write and self._controller.create_cita_flow(self.calendar.selectedDate().toString("yyyy-MM-dd")):
            self._refresh_calendario()
            self._programar_refresco_lista()

    def _on_delete(self) -> None:
        cita_id = self._selected_id()
        if self._can_write and cita_id and self._controller.delete_cita(cita_id):
            self._refresh_calendario()
            self._programar_refresco_lista()

    def _abrir_dialogo_recordatorio(self, cita_id: int) -> None:
        RecordatorioCitaDialog(self._container, self._i18n, cita_id, self).exec()

    def _abrir_dialogo_riesgo(self, cita_id: int) -> None:
        explicacion = self._container.prediccion_ausencias_facade.obtener_explicacion_riesgo_uc.ejecutar(cita_id)
        salud = self._container.prediccion_ausencias_facade.obtener_salud_uc.ejecutar()
        dialog = RiesgoAusenciaDialog(self._i18n, explicacion, salud, self)
        dialog.exec()
