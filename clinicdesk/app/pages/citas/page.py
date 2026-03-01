from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional

from PySide6.QtCore import QDate, QSettings, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDateEdit,
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
from clinicdesk.app.application.citas_filtros_validacion import (
    normalizar_filtros_citas,
    resolver_columnas_cita,
    validar_filtros_citas,
)
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.container import AppContainer
from clinicdesk.app.controllers.citas_controller import CitasController
from clinicdesk.app.domain.citas_atributos import ATRIBUTOS_CITA
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.estado_cita_presentacion import ESTADOS_FILTRO_CITAS, etiqueta_estado_cita
from clinicdesk.app.pages.citas.recordatorio_cita_dialog import RecordatorioCitaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_dialog import RiesgoAusenciaDialog
from clinicdesk.app.pages.citas.riesgo_ausencia_ui import (
    SETTINGS_KEY_RIESGO_AGENDA,
    construir_dtos_desde_calendario,
    construir_dtos_desde_listado,
    resolver_texto_riesgo,
    tooltip_riesgo,
)
from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget
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
        self._columnas_restauradas = False
        self._columnas_lista = self._cargar_columnas_lista()

        self._build_ui()
        self._bind_events()
        self._set_hoy()
        self._refresh_calendario()
        self._programar_refresco_lista()

    def _build_ui(self) -> None:
        self.tabs = QTabWidget(self)
        self.calendar = QCalendarWidget()
        self.lbl_date = QLabel("Fecha: —")
        self.btn_new = QPushButton("Nueva cita")
        self.btn_delete = QPushButton("Eliminar cita")
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
        self.filtros = FiltroListadoWidget(tab_lista)
        self.filtros.set_estado_items(ESTADOS_FILTRO_CITAS, default_value="TODOS")
        self.btn_hoy = QPushButton("Hoy")
        self.btn_semana = QPushButton("Semana")
        self.btn_mes = QPushButton("Mes")
        self.desde_date = QDateEdit(tab_lista)
        self.desde_date.setCalendarPopup(True)
        self.hasta_date = QDateEdit(tab_lista)
        self.hasta_date.setCalendarPopup(True)
        self.lbl_cargando = QLabel("", tab_lista)
        self.lbl_error_filtros = QLabel("", tab_lista)
        self.lbl_error_filtros.setObjectName("citas-filtros-error")
        self.lbl_aviso_prediccion = QLabel("", tab_lista)
        self.btn_ir_prediccion = QPushButton(self._i18n.t("citas.riesgo.ir_prediccion"), tab_lista)
        self.btn_ir_prediccion.clicked.connect(self._ir_a_prediccion)
        self.btn_ir_prediccion.setVisible(False)
        self.table_lista = self._crear_tabla_lista()

        barra_rango = QHBoxLayout()
        barra_rango.addWidget(QLabel("Desde"))
        barra_rango.addWidget(self.desde_date)
        barra_rango.addWidget(QLabel("Hasta"))
        barra_rango.addWidget(self.hasta_date)
        barra_rango.addWidget(self.btn_hoy)
        barra_rango.addWidget(self.btn_semana)
        barra_rango.addWidget(self.btn_mes)
        barra_rango.addStretch(1)
        barra_rango.addWidget(self.lbl_cargando)

        barra_aviso = QHBoxLayout()
        barra_aviso.addWidget(self.lbl_error_filtros)
        barra_aviso.addWidget(self.lbl_aviso_prediccion)
        barra_aviso.addWidget(self.btn_ir_prediccion)
        barra_aviso.addStretch(1)

        layout_lista = QVBoxLayout(tab_lista)
        layout_lista.addWidget(self.filtros)
        layout_lista.addLayout(barra_rango)
        layout_lista.addLayout(barra_aviso)
        layout_lista.addWidget(self.table_lista)

        self.tabs.addTab(tab_calendario, "Calendario")
        self.tabs.addTab(tab_lista, "Lista")
        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

    def _crear_tabla_calendario(self) -> QTableWidget:
        tabla = QTableWidget(0, 8)
        tabla.setHorizontalHeaderLabels(["ID", "Inicio", "Fin", "Paciente", "Médico", "Sala", "Estado", "Motivo"])
        tabla.setColumnHidden(0, True)
        tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        return tabla

    def _crear_tabla_lista(self) -> QTableWidget:
        tabla = QTableWidget(0, len(self._columnas_lista))
        tabla.setHorizontalHeaderLabels(self._headers_lista(self._columnas_lista))
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
        self.filtros.filtros_cambiados.connect(self._programar_refresco_lista)
        self.desde_date.dateChanged.connect(self._programar_refresco_lista)
        self.hasta_date.dateChanged.connect(self._programar_refresco_lista)
        self.btn_hoy.clicked.connect(self._set_hoy)
        self.btn_semana.clicked.connect(self._set_semana)
        self.btn_mes.clicked.connect(self._set_mes)
        self.table_lista.itemClicked.connect(self._on_lista_item_clicked)
        self.table_lista.customContextMenuRequested.connect(self._on_lista_context_menu)

    def on_show(self) -> None:
        if self._columnas_restauradas:
            self.lbl_error_filtros.setText(self._i18n.t("citas.validacion.columnas_invalidas_restauradas"))
        self._riesgo_enabled = self._mostrar_riesgo_agenda()
        self._sync_columna_riesgo_lista()
        self._refresh_calendario()
        self._programar_refresco_lista()

    def _mostrar_riesgo_agenda(self) -> bool:
        value = QSettings("clinicdesk", "ui").value(SETTINGS_KEY_RIESGO_AGENDA, 0)
        return bool(int(value))

    def _sync_columna_riesgo_lista(self) -> None:
        headers = self._headers_lista(self._columnas_lista)
        if self._riesgo_enabled:
            headers.append(self._i18n.t("citas.riesgo.columna"))
        self.table_lista.setColumnCount(len(headers))
        self.table_lista.setHorizontalHeaderLabels(headers)

    def _on_calendario_change(self) -> None:
        self._refresh_calendario()
        selected = self.calendar.selectedDate()
        self.desde_date.setDate(selected)
        self.hasta_date.setDate(selected)
        self._programar_refresco_lista()

    def _refresh_calendario(self) -> None:
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.lbl_date.setText(f"Fecha: {date_str}")
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
                if self._riesgo_enabled:
                    item.setToolTip(tooltip_riesgo(riesgos.get(c.id, RIESGO_NO_DISPONIBLE), self._i18n))
                self.table.setItem(row_index, col, item)

    def _obtener_riesgo_citas_calendario(self, rows: list[CitaRow]) -> dict[int, str]:
        dtos = construir_dtos_desde_calendario(rows, datetime.now())
        riesgos = self._container.prediccion_ausencias_facade.obtener_riesgo_agenda_uc.ejecutar(dtos)
        self._registrar_predicciones_agenda(riesgos)
        return riesgos

    def _programar_refresco_lista(self) -> None:
        self.lbl_cargando.setText("Cargando...")
        QTimer.singleShot(0, self._refresh_lista)

    def _refresh_lista(self) -> None:
        filtros_norm = normalizar_filtros_citas(
            {
                "desde": self.desde_date.date().toString("yyyy-MM-dd"),
                "hasta": self.hasta_date.date().toString("yyyy-MM-dd"),
                "texto_busqueda": self.filtros.texto(),
                "estado": self.filtros.estado(),
            }
        )
        resultado = validar_filtros_citas(filtros_norm)
        if not resultado.ok:
            self._mostrar_error_validacion(resultado)
            self._cargar_tabla_lista([])
            self.filtros.set_contador(0, 0)
            self.lbl_cargando.setText("")
            return

        self.lbl_error_filtros.setText("")
        rows = self._queries.search_listado(
            desde=filtros_norm["desde"],
            hasta=filtros_norm["hasta"],
            texto=filtros_norm["texto_busqueda"] or "",
            estado=filtros_norm["estado"] or "TODOS",
        )
        self._cargar_tabla_lista(rows)
        self.filtros.set_contador(len(rows), len(rows))
        self.lbl_cargando.setText("")

    def _cargar_tabla_lista(self, rows: list[CitaListadoRow]) -> None:
        riesgos = self._obtener_riesgo_citas_lista(rows) if self._riesgo_enabled else {}
        self._citas_lista_ids = [cita.id for cita in rows]
        self.table_lista.setRowCount(0)
        hay_no_disponible = False
        for cita in rows:
            row_index = self.table_lista.rowCount()
            self.table_lista.insertRow(row_index)
            values = [
                self._valor_columna_lista(clave, cita) for clave in self._columnas_lista
            ]
            if self._riesgo_enabled:
                resultado = resolver_texto_riesgo(riesgos.get(cita.id, RIESGO_NO_DISPONIBLE), self._i18n)
                values.append(resultado.texto)
                hay_no_disponible = hay_no_disponible or resultado.no_disponible
            for col, value in enumerate(values):
                self.table_lista.setItem(row_index, col, QTableWidgetItem(value))
        self._actualizar_aviso_no_disponible(hay_no_disponible)

    def _mostrar_error_validacion(self, resultado) -> None:
        mensaje = self._i18n.t(resultado.errores[0].i18n_key)
        self.lbl_error_filtros.setText(mensaje)

    def _valor_columna_lista(self, clave: str, cita: CitaListadoRow) -> str:
        mapa = {
            "fecha": cita.fecha,
            "hora_inicio": cita.hora_inicio,
            "hora_fin": cita.hora_fin,
            "paciente": cita.paciente,
            "medico": cita.medico,
            "sala": cita.sala,
            "estado": etiqueta_estado_cita(cita.estado),
            "notas_len": str(cita.notas_len),
            "incidencias": self._i18n.t("comun.si") if cita.tiene_incidencias else self._i18n.t("comun.no"),
        }
        return mapa.get(clave, "")

    def _headers_lista(self, columnas: list[str]) -> list[str]:
        etiquetas = {atributo.clave: atributo.etiqueta for atributo in ATRIBUTOS_CITA}
        return [etiquetas[clave] for clave in columnas]

    def _cargar_columnas_lista(self) -> list[str]:
        qsettings = QSettings("clinicdesk", "ui")
        raw = qsettings.value("citas/listado/columnas")
        columnas = self._normalizar_columnas(raw)
        resultado = resolver_columnas_cita(columnas)
        self._columnas_restauradas = resultado.restauradas
        if resultado.restauradas:
            qsettings.setValue("citas/listado/columnas", list(resultado.columnas))
        return list(resultado.columnas)

    @staticmethod
    def _normalizar_columnas(raw) -> list[str] | None:
        if raw is None:
            return None
        if isinstance(raw, str):
            return [parte.strip() for parte in raw.split(",") if parte.strip()]
        if isinstance(raw, list):
            return [str(parte).strip() for parte in raw if str(parte).strip()]
        return None

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
        return self.table_lista.columnCount() - 1

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

    def _set_hoy(self) -> None:
        today = QDate.currentDate()
        self.desde_date.setDate(today)
        self.hasta_date.setDate(today)
        self._programar_refresco_lista()

    def _set_semana(self) -> None:
        today = date.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        self.desde_date.setDate(QDate(start.year, start.month, start.day))
        self.hasta_date.setDate(QDate(end.year, end.month, end.day))
        self._programar_refresco_lista()

    def _set_mes(self) -> None:
        today = date.today()
        start = today.replace(day=1)
        end = today.replace(day=31) if today.month == 12 else today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        self.desde_date.setDate(QDate(start.year, start.month, start.day))
        self.hasta_date.setDate(QDate(end.year, end.month, end.day))
        self._programar_refresco_lista()

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
