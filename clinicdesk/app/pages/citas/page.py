from __future__ import annotations

from datetime import datetime
from typing import List, Optional

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

from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import RIESGO_NO_DISPONIBLE
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.container import AppContainer
from clinicdesk.app.controllers.citas_controller import CitasController
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.estado_cita_presentacion import ESTADOS_FILTRO_CITAS, etiqueta_estado_cita
from clinicdesk.app.pages.citas.atributos_cita import (
    ATRIBUTOS_CITA,
    claves_tooltip_por_defecto,
    valor_calendario_por_clave,
    valor_lista_por_clave,
)
from clinicdesk.app.pages.citas.dialogs.selector_columnas_citas_dialog import SelectorColumnasCitasDialog
from clinicdesk.app.pages.citas.panel_filtros_citas_widget import PanelFiltrosCitasWidget
from clinicdesk.app.pages.citas.preferencias_citas import PreferenciasCitasStore
from clinicdesk.app.pages.citas.recordatorio_cita_dialog import RecordatorioCitaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_dialog import RiesgoAusenciaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_ui import (
    SETTINGS_KEY_RIESGO_AGENDA,
    construir_dtos_desde_calendario,
    construir_dtos_desde_listado,
    resolver_texto_riesgo,
)
from clinicdesk.app.queries.citas_queries import CitaListadoRow, CitaRow, CitasQueries


LOGGER = get_logger(__name__)


class PageCitas(QWidget):
    def __init__(self, container: AppContainer, i18n: I18nManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._i18n = i18n
        self._queries = CitasQueries(container)
        self._controller = CitasController(self, container)
        self._can_write = container.user_context.can_write
        self._riesgo_enabled = False
        self._citas_lista_ids: list[int] = []
        self._columnas_visibles: list[str] = []
        self._preferencias = PreferenciasCitasStore(container.user_context.username)

        self._build_ui()
        self._bind_events()
        self._cargar_preferencias()
        self._sync_columna_riesgo_lista()
        self._refresh_calendario()
        self._programar_refresco_lista()

    def _build_ui(self) -> None:
        self.panel_filtros = PanelFiltrosCitasWidget(self._i18n, self)
        self.panel_filtros.set_estado_items(ESTADOS_FILTRO_CITAS, default_value="TODOS")
        self.tabs = QTabWidget(self)
        self.calendar = QCalendarWidget()
        self.lbl_date = QLabel(self._i18n.t("citas.calendario.fecha_vacia"))
        self.btn_new = QPushButton(self._i18n.t("citas.acciones.nueva"))
        self.btn_delete = QPushButton(self._i18n.t("citas.acciones.eliminar"))
        self.btn_new.setEnabled(self._can_write)
        self.btn_delete.setEnabled(False)
        self.table = self._crear_tabla_calendario()

        tab_calendario = QWidget(self)
        panel_izquierdo = QVBoxLayout()
        panel_izquierdo.addWidget(self.calendar)
        panel_izquierdo.addWidget(self.lbl_date)
        panel_izquierdo.addWidget(self.btn_new)
        panel_izquierdo.addWidget(self.btn_delete)

        panel_derecho = QVBoxLayout()
        panel_derecho.addWidget(self.table)
        layout_calendario = QHBoxLayout(tab_calendario)
        layout_calendario.addLayout(panel_izquierdo, 1)
        layout_calendario.addLayout(panel_derecho, 3)

        tab_lista = QWidget(self)
        self.lbl_cargando = QLabel("", tab_lista)
        self.lbl_estado_lista = QLabel("", tab_lista)
        self.lbl_aviso_prediccion = QLabel("", tab_lista)
        self.btn_ir_prediccion = QPushButton(self._i18n.t("citas.riesgo.ir_prediccion"), tab_lista)
        self.btn_columnas = QPushButton(self._i18n.t("citas.columnas.boton"), tab_lista)
        self.btn_ir_prediccion.clicked.connect(self._ir_a_prediccion)
        self.btn_ir_prediccion.setVisible(False)
        self.table_lista = self._crear_tabla_lista()
        self.lbl_resumen_lista = QLabel(self._i18n.t("citas.lista.mostrando").format(mostrados=0, totales=0), tab_lista)

        barra_aviso = QHBoxLayout()
        barra_aviso.addWidget(self.btn_columnas)
        barra_aviso.addWidget(self.lbl_estado_lista)
        barra_aviso.addWidget(self.lbl_aviso_prediccion)
        barra_aviso.addWidget(self.btn_ir_prediccion)
        barra_aviso.addStretch(1)
        barra_aviso.addWidget(self.lbl_cargando)

        layout_lista = QVBoxLayout(tab_lista)
        layout_lista.addLayout(barra_aviso)
        layout_lista.addWidget(self.table_lista)
        layout_lista.addWidget(self.lbl_resumen_lista)

        self.tabs.addTab(tab_calendario, self._i18n.t("citas.tab.calendario"))
        self.tabs.addTab(tab_lista, self._i18n.t("citas.tab.lista"))
        root = QVBoxLayout(self)
        root.addWidget(self.panel_filtros)
        root.addWidget(self.tabs)

    def _crear_tabla_calendario(self) -> QTableWidget:
        tabla = QTableWidget(0, 8)
        tabla.setHorizontalHeaderLabels([
            self._i18n.t("citas.atributo.id"),
            self._i18n.t("citas.atributo.inicio"),
            self._i18n.t("citas.atributo.fin"),
            self._i18n.t("citas.atributo.paciente"),
            self._i18n.t("citas.atributo.medico"),
            self._i18n.t("citas.atributo.sala"),
            self._i18n.t("citas.atributo.estado"),
            self._i18n.t("citas.atributo.motivo"),
        ])
        tabla.setColumnHidden(0, True)
        tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        return tabla

    def _crear_tabla_lista(self) -> QTableWidget:
        tabla = QTableWidget(0, 0)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        return tabla

    def _bind_events(self) -> None:
        self.calendar.selectionChanged.connect(self._on_calendario_change)
        self.btn_new.clicked.connect(self._on_new)
        self.btn_delete.clicked.connect(self._on_delete)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_calendario_item_double_clicked)
        self.table.customContextMenuRequested.connect(self._on_calendario_context_menu)
        self.panel_filtros.filtros_aplicar.connect(self._programar_refresco_lista)
        self.panel_filtros.filtros_limpiar.connect(self._programar_refresco_lista)
        self.btn_columnas.clicked.connect(self._abrir_selector_columnas)
        self.table_lista.itemClicked.connect(self._on_lista_item_clicked)
        self.table_lista.customContextMenuRequested.connect(self._on_lista_context_menu)

    def on_show(self) -> None:
        self._riesgo_enabled = self._mostrar_riesgo_agenda()
        self._cargar_preferencias()
        self._sync_columna_riesgo_lista()
        self._refresh_calendario()
        self._programar_refresco_lista()

    def _mostrar_riesgo_agenda(self) -> bool:
        value = QSettings("clinicdesk", "ui").value(SETTINGS_KEY_RIESGO_AGENDA, 0)
        return bool(int(value))

    def _sync_columna_riesgo_lista(self) -> None:
        self._sincronizar_columnas_visibles()

    def _on_calendario_change(self) -> None:
        self._refresh_calendario()
        self.panel_filtros.desde_date.setDate(self.calendar.selectedDate())
        self.panel_filtros.hasta_date.setDate(self.calendar.selectedDate())

    def _refresh_calendario(self) -> None:
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.lbl_date.setText(self._i18n.t("citas.calendario.fecha").format(fecha=date_str))
        rows: List[CitaRow] = self._queries.list_by_date(date_str)
        riesgos = self._obtener_riesgo_citas_calendario(rows) if self._riesgo_enabled else {}
        self.table.setRowCount(0)
        for c in rows:
            row_index = self.table.rowCount()
            self.table.insertRow(row_index)
            values = [
                str(c.id),
                c.inicio,
                c.fin,
                c.paciente_nombre,
                c.medico_nombre,
                c.sala_nombre,
                etiqueta_estado_cita(c.estado),
                c.motivo or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(self._tooltip_calendario(c, riesgos.get(c.id, RIESGO_NO_DISPONIBLE)))
                self.table.setItem(row_index, col, item)

    def _obtener_riesgo_citas_calendario(self, rows: list[CitaRow]) -> dict[int, str]:
        dtos = construir_dtos_desde_calendario(rows, datetime.now())
        riesgos = self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc.ejecutar(dtos)
        self._registrar_predicciones_agenda(riesgos)
        return riesgos

    def _programar_refresco_lista(self) -> None:
        self.lbl_cargando.setText(self._i18n.t("citas.estado.cargando"))
        self.panel_filtros.setEnabled(False)
        self.btn_columnas.setEnabled(False)
        QTimer.singleShot(0, self._refresh_lista)

    def _refresh_lista(self) -> None:
        rows = self._queries.search_listado(
            desde=self.panel_filtros.desde_date.date().toString("yyyy-MM-dd"),
            hasta=self.panel_filtros.hasta_date.date().toString("yyyy-MM-dd"),
            texto=self.panel_filtros.txt_busqueda.text().strip(),
            estado=self.panel_filtros.cbo_estado.currentData() or "TODOS",
        )
        self._cargar_tabla_lista(rows)
        self.lbl_resumen_lista.setText(self._i18n.t("citas.lista.mostrando").format(mostrados=len(rows), totales=len(rows)))
        if rows:
            self.lbl_estado_lista.setText("")
        else:
            self.lbl_estado_lista.setText(self._i18n.t("citas.estado.vacio"))
        self._guardar_filtros()
        self.lbl_cargando.setText("")
        self.panel_filtros.setEnabled(True)
        self.btn_columnas.setEnabled(True)

    def _cargar_tabla_lista(self, rows: list[CitaListadoRow]) -> None:
        riesgos = self._obtener_riesgo_citas_lista(rows) if self._riesgo_enabled else {}
        self._citas_lista_ids = [cita.id for cita in rows]
        self.table_lista.setRowCount(0)
        hay_no_disponible = False
        for cita in rows:
            row_index = self.table_lista.rowCount()
            self.table_lista.insertRow(row_index)
            resultado = resolver_texto_riesgo(riesgos.get(cita.id, RIESGO_NO_DISPONIBLE), self._i18n)
            hay_no_disponible = hay_no_disponible or resultado.no_disponible
            values = [
                valor_lista_por_clave(cita, clave, i18n=self._i18n, riesgo=resultado.texto)
                for clave in self._columnas_visibles
            ]
            for col, value in enumerate(values):
                self.table_lista.setItem(row_index, col, QTableWidgetItem(value))
        self._actualizar_aviso_no_disponible(hay_no_disponible)

    def _obtener_riesgo_citas_lista(self, rows: list[CitaListadoRow]) -> dict[int, str]:
        dtos = construir_dtos_desde_listado(rows, datetime.now())
        riesgos = self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc.ejecutar(dtos)
        self._registrar_predicciones_agenda(riesgos)
        return riesgos

    def _registrar_predicciones_agenda(self, riesgos: dict[int, str]) -> None:
        metadata = self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc.almacenamiento.cargar_metadata()
        if metadata is None:
            return
        try:
            self._container.prediccion_ausencias_facade.registrar_predicciones_agenda_uc.ejecutar(
                metadata.fecha_entrenamiento,
                riesgos,
                source="agenda",
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning(
                "registro_predicciones_agenda_fallido",
                extra={"reason_code": "prediction_log_failed", "error": str(exc)},
            )

    def _actualizar_aviso_no_disponible(self, visible: bool) -> None:
        mostrar = self._riesgo_enabled and visible
        self.lbl_aviso_prediccion.setText(self._i18n.t("citas.riesgo.aviso_no_disponible") if mostrar else "")
        self.btn_ir_prediccion.setVisible(mostrar)

    def _on_lista_item_clicked(self, item: QTableWidgetItem) -> None:
        if not self._riesgo_enabled or item.column() != self._columna_riesgo_lista():
            return
        cita_id = self._cita_id_lista(item.row())
        if cita_id is not None:
            self._abrir_dialogo_riesgo(cita_id)

    def _on_calendario_item_double_clicked(self, item: QTableWidgetItem) -> None:
        if not self._riesgo_enabled:
            return
        cita_id = self._cita_id_calendario(item.row())
        if cita_id is not None:
            self._abrir_dialogo_riesgo(cita_id)


    def _on_lista_context_menu(self, point) -> None:
        item = self.table_lista.itemAt(point)
        if item is None:
            return
        cita_id = self._cita_id_lista(item.row())
        if cita_id is None:
            return
        menu = QMenu(self)
        action_recordatorio = QAction(self._i18n.t("recordatorio.accion.preparar"), self)
        action_recordatorio.triggered.connect(lambda: self._abrir_dialogo_recordatorio(cita_id))
        menu.addAction(action_recordatorio)
        if self._riesgo_enabled:
            action_riesgo = QAction(self._i18n.t("citas.riesgo_dialogo.menu.ver_riesgo"), self)
            action_riesgo.triggered.connect(lambda: self._abrir_dialogo_riesgo(cita_id))
            menu.addAction(action_riesgo)
        menu.exec(self.table_lista.mapToGlobal(point))

    def _on_calendario_context_menu(self, point) -> None:
        item = self.table.itemAt(point)
        if item is None:
            return
        cita_id = self._cita_id_calendario(item.row())
        if cita_id is None:
            return
        menu = QMenu(self)
        action_recordatorio = QAction(self._i18n.t("recordatorio.accion.preparar"), self)
        action_recordatorio.triggered.connect(lambda: self._abrir_dialogo_recordatorio(cita_id))
        menu.addAction(action_recordatorio)
        if self._riesgo_enabled:
            action_riesgo = QAction(self._i18n.t("citas.riesgo_dialogo.menu.ver_riesgo"), self)
            action_riesgo.triggered.connect(lambda: self._abrir_dialogo_riesgo(cita_id))
            menu.addAction(action_riesgo)
        menu.exec(self.table.mapToGlobal(point))

    def _abrir_dialogo_riesgo(self, cita_id: int) -> None:
        explicacion = self._container.prediccion_ausencias_facade.obtener_explicacion_riesgo_uc.ejecutar(cita_id)
        salud = self._container.prediccion_ausencias_facade.obtener_salud_uc.ejecutar()
        dialog = RiesgoAusenciaDialog(self._i18n, explicacion, salud, self)
        dialog.btn_preparar_recordatorio.clicked.connect(lambda: self._abrir_dialogo_recordatorio(cita_id))
        dialog.btn_ir_prediccion.clicked.connect(self._ir_a_prediccion)
        dialog.exec()

    def _abrir_dialogo_recordatorio(self, cita_id: int) -> None:
        dialog = RecordatorioCitaDialog(self._container, self._i18n, cita_id, self)
        dialog.exec()

    def _columna_riesgo_lista(self) -> int:
        try:
            return self._columnas_visibles.index("riesgo")
        except ValueError:
            return -1

    def _cita_id_lista(self, row: int) -> int | None:
        if row < 0 or row >= len(self._citas_lista_ids):
            return None
        return self._citas_lista_ids[row]

    def _cita_id_calendario(self, row: int) -> int | None:
        item = self.table.item(row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def _ir_a_prediccion(self) -> None:
        window = self.window()
        if hasattr(window, "navigate"):
            window.navigate("prediccion_ausencias")

    def _cargar_preferencias(self) -> None:
        preferencias = self._preferencias.cargar()
        if preferencias.filtros.desde and preferencias.filtros.hasta:
            self.panel_filtros.aplicar_estado(preferencias.filtros)
        else:
            self.panel_filtros.set_hoy()
        self._columnas_visibles = preferencias.columnas

    def _guardar_filtros(self) -> None:
        self._preferencias.guardar_filtros(self.panel_filtros.estado_actual())

    def _sincronizar_columnas_visibles(self) -> None:
        columnas = []
        for atributo in ATRIBUTOS_CITA:
            if atributo.clave == "riesgo" and not self._riesgo_enabled:
                continue
            if atributo.clave in self._columnas_visibles:
                columnas.append(atributo)
        if not columnas:
            columnas = [a for a in ATRIBUTOS_CITA if a.visible_por_defecto and (a.clave != "riesgo" or self._riesgo_enabled)]
        self._columnas_visibles = [col.clave for col in columnas]
        self.table_lista.setColumnCount(len(columnas))
        self.table_lista.setHorizontalHeaderLabels([self._i18n.t(col.clave_i18n) for col in columnas])

    def _abrir_selector_columnas(self) -> None:
        dialog = SelectorColumnasCitasDialog(self._i18n, self._columnas_visibles, self)
        if dialog.exec() != dialog.Accepted:
            return
        self._columnas_visibles = dialog.columnas_seleccionadas()
        self._preferencias.guardar_columnas(self._columnas_visibles)
        self._sync_columna_riesgo_lista()
        self._programar_refresco_lista()

    def _tooltip_calendario(self, cita: CitaRow, riesgo: str) -> str:
        lineas = []
        for clave in claves_tooltip_por_defecto():
            if clave == "riesgo" and not self._riesgo_enabled:
                continue
            etiqueta = next((self._i18n.t(a.clave_i18n) for a in ATRIBUTOS_CITA if a.clave == clave), "")
            valor = valor_calendario_por_clave(cita, clave, i18n=self._i18n, riesgo=riesgo)
            if valor:
                lineas.append(f"{etiqueta}: {valor}")
        if not lineas:
            return self._i18n.t("citas.tooltip.sin_detalles")
        return "\n".join(lineas)

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

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
