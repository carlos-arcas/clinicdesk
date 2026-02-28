from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

import logging

from PySide6.QtCore import QDate, Qt, QTimer
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

from clinicdesk.app.container import AppContainer
from clinicdesk.app.controllers.citas_controller import CitasController
from clinicdesk.app.pages.citas.estado_cita_presentacion import (
    ESTADOS_FILTRO_CITAS,
    etiqueta_estado_cita,
)
from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget
from clinicdesk.app.queries.citas_queries import CitaListadoRow, CitaRow, CitasQueries


class PageCitas(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = CitasQueries(container)
        self._controller = CitasController(self, container)
        self._can_write = container.user_context.can_write

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

        layout_lista = QVBoxLayout(tab_lista)
        layout_lista.addWidget(self.filtros)
        layout_lista.addLayout(barra_rango)
        layout_lista.addWidget(self.table_lista)

        self.tabs.addTab(tab_calendario, "Calendario")
        self.tabs.addTab(tab_lista, "Lista")

        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

    def _crear_tabla_calendario(self) -> QTableWidget:
        tabla = QTableWidget(0, 8)
        tabla.setHorizontalHeaderLabels(
            ["ID", "Inicio", "Fin", "Paciente", "Médico", "Sala", "Estado", "Motivo"]
        )
        tabla.setColumnHidden(0, True)
        tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        return tabla

    def _crear_tabla_lista(self) -> QTableWidget:
        tabla = QTableWidget(0, 9)
        tabla.setHorizontalHeaderLabels(
            [
                "Fecha",
                "Hora inicio",
                "Hora fin",
                "Paciente",
                "Médico",
                "Sala",
                "Estado",
                "Notas len",
                "Incidencias",
            ]
        )
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        return tabla

    def _bind_events(self) -> None:
        self.calendar.selectionChanged.connect(self._on_calendario_change)
        self.btn_new.clicked.connect(self._on_new)
        self.btn_delete.clicked.connect(self._on_delete)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.filtros.filtros_cambiados.connect(self._programar_refresco_lista)
        self.desde_date.dateChanged.connect(self._programar_refresco_lista)
        self.hasta_date.dateChanged.connect(self._programar_refresco_lista)
        self.btn_hoy.clicked.connect(self._set_hoy)
        self.btn_semana.clicked.connect(self._set_semana)
        self.btn_mes.clicked.connect(self._set_mes)

    def on_show(self) -> None:
        self._refresh_calendario()
        self._programar_refresco_lista()

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
        self.table.setRowCount(0)
        for c in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(r, 1, QTableWidgetItem(c.inicio))
            self.table.setItem(r, 2, QTableWidgetItem(c.fin))
            self.table.setItem(r, 3, QTableWidgetItem(c.paciente_nombre))
            self.table.setItem(r, 4, QTableWidgetItem(c.medico_nombre))
            self.table.setItem(r, 5, QTableWidgetItem(c.sala_nombre))
            self.table.setItem(r, 6, QTableWidgetItem(etiqueta_estado_cita(c.estado)))
            self.table.setItem(r, 7, QTableWidgetItem(c.motivo or ""))

    def _programar_refresco_lista(self) -> None:
        self.lbl_cargando.setText("Cargando...")
        QTimer.singleShot(0, self._refresh_lista)

    def _refresh_lista(self) -> None:
        desde = self.desde_date.date().toString("yyyy-MM-dd")
        hasta = self.hasta_date.date().toString("yyyy-MM-dd")
        texto = self.filtros.texto()
        estado = self.filtros.estado()
        rows = self._queries.search_listado(desde=desde, hasta=hasta, texto=texto, estado=estado)
        self._cargar_tabla_lista(rows)
        self.filtros.set_contador(len(rows), len(rows))
        self.lbl_cargando.setText("")

    def _cargar_tabla_lista(self, rows: list[CitaListadoRow]) -> None:
        self.table_lista.setRowCount(0)
        for cita in rows:
            row = self.table_lista.rowCount()
            self.table_lista.insertRow(row)
            self.table_lista.setItem(row, 0, QTableWidgetItem(cita.fecha))
            self.table_lista.setItem(row, 1, QTableWidgetItem(cita.hora_inicio))
            self.table_lista.setItem(row, 2, QTableWidgetItem(cita.hora_fin))
            self.table_lista.setItem(row, 3, QTableWidgetItem(cita.paciente))
            self.table_lista.setItem(row, 4, QTableWidgetItem(cita.medico))
            self.table_lista.setItem(row, 5, QTableWidgetItem(cita.sala))
            self.table_lista.setItem(row, 6, QTableWidgetItem(etiqueta_estado_cita(cita.estado)))
            self.table_lista.setItem(row, 7, QTableWidgetItem(str(cita.notas_len)))
            self.table_lista.setItem(row, 8, QTableWidgetItem("Sí" if cita.tiene_incidencias else "No"))

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
        if today.month == 12:
            end = today.replace(day=31)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
            end = next_month - timedelta(days=1)
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
        if not self._can_write:
            return
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        if self._controller.create_cita_flow(date_str):
            self._refresh_calendario()
            self._programar_refresco_lista()

    def _on_delete(self) -> None:
        if not self._can_write:
            return
        cita_id = self._selected_id()
        if not cita_id:
            return
        if self._controller.delete_cita(cita_id):
            self._refresh_calendario()
            self._programar_refresco_lista()

    def _open_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        menu = QMenu(self)
        action_new = menu.addAction("Nueva cita")
        action_delete = menu.addAction("Eliminar cita")
        action_new.setEnabled(self._can_write)
        action_delete.setEnabled(self._can_write and self._selected_id() is not None)
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == action_new:
            self._on_new()
        elif action == action_delete:
            self._on_delete()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)
