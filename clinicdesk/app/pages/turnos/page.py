from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDialog,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.shared.table_utils import apply_row_style, set_item
from clinicdesk.app.pages.turnos.dialogs.bloque_form import BloqueFormDialog
from clinicdesk.app.pages.shared.selector_dialog import select_medico, select_personal
from clinicdesk.app.queries.turnos_queries import TurnosQueries, CalendarioRow
from clinicdesk.app.infrastructure.sqlite.repos_calendario_medico import BloqueCalendarioMedico
from clinicdesk.app.infrastructure.sqlite.repos_calendario_personal import BloqueCalendarioPersonal


class PageTurnos(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = TurnosQueries(container.connection)
        self._persona_id: Optional[int] = None

        self._build_ui()
        self._connect_signals()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.cbo_tipo = QComboBox()
        self.cbo_tipo.addItems(["Médico", "Personal"])
        self.txt_persona = QLineEdit()
        self.txt_persona.setReadOnly(True)
        self.btn_persona = QPushButton("Buscar…")
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addMonths(-1))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate().addMonths(1))
        self.btn_cargar = QPushButton("Cargar")

        filters.addWidget(QLabel("Tipo"))
        filters.addWidget(self.cbo_tipo)
        filters.addWidget(QLabel("Persona"))
        filters.addWidget(self.txt_persona)
        filters.addWidget(self.btn_persona)
        filters.addWidget(QLabel("Desde"))
        filters.addWidget(self.date_desde)
        filters.addWidget(QLabel("Hasta"))
        filters.addWidget(self.date_hasta)
        filters.addWidget(self.btn_cargar)

        actions = QHBoxLayout()
        self.btn_nuevo = QPushButton("Añadir bloque")
        self.btn_eliminar = QPushButton("Eliminar bloque")
        self.btn_eliminar.setEnabled(False)
        actions.addWidget(self.btn_nuevo)
        actions.addWidget(self.btn_eliminar)
        actions.addStretch(1)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Turno", "Inicio", "Fin", "Observaciones", "Activo"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        root.addLayout(filters)
        root.addLayout(actions)
        root.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.cbo_tipo.currentTextChanged.connect(self._reset_persona)
        self.btn_persona.clicked.connect(self._select_persona)
        self.btn_cargar.clicked.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_eliminar.clicked.connect(self._on_eliminar)
        self.table.customContextMenuRequested.connect(self._open_context_menu)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        persona_id = self._persona_id
        if persona_id is None:
            self.table.setRowCount(0)
            return

        desde = self.date_desde.date().toString("yyyy-MM-dd")
        hasta = self.date_hasta.date().toString("yyyy-MM-dd")

        if self.cbo_tipo.currentText() == "Médico":
            rows = self._queries.list_calendario_medico(persona_id, desde=desde, hasta=hasta)
        else:
            rows = self._queries.list_calendario_personal(persona_id, desde=desde, hasta=hasta)

        self._render(rows)

    def _render(self, rows: list[CalendarioRow]) -> None:
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            set_item(self.table, row, 0, str(r.id))
            set_item(self.table, row, 1, r.fecha)
            set_item(self.table, row, 2, r.turno)
            set_item(self.table, row, 3, r.hora_inicio)
            set_item(self.table, row, 4, r.hora_fin)
            set_item(self.table, row, 5, r.observaciones)
            set_item(self.table, row, 6, "Sí" if r.activo else "No")
            tooltip = (
                f"Fecha: {r.fecha}\n"
                f"Turno: {r.turno}\n"
                f"Horario: {r.hora_inicio} - {r.hora_fin}\n"
                f"Observaciones: {r.observaciones or '—'}\n"
                f"Estado: {'Activo' if r.activo else 'Inactivo'}"
            )
            apply_row_style(self.table, row, inactive=not r.activo, tooltip=tooltip)

    def _on_selection_changed(self) -> None:
        self.btn_eliminar.setEnabled(self._selected_id() is not None)

    def _on_nuevo(self) -> None:
        persona_id = self._persona_id
        if persona_id is None:
            QMessageBox.warning(self, "Turnos", "Selecciona una persona.")
            return

        turnos = self._container.turnos_repo.list_all(solo_activos=True)
        dialog = BloqueFormDialog(turnos, self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return

        if self.cbo_tipo.currentText() == "Médico":
            bloque = BloqueCalendarioMedico(
                medico_id=persona_id,
                fecha=data.fecha,
                turno_id=data.turno_id,
                hora_inicio_override=data.hora_inicio_override,
                hora_fin_override=data.hora_fin_override,
                observaciones=data.observaciones,
                activo=data.activo,
            )
            self._container.calendario_medico_repo.create(bloque)
        else:
            bloque = BloqueCalendarioPersonal(
                personal_id=persona_id,
                fecha=data.fecha,
                turno_id=data.turno_id,
                hora_inicio_override=data.hora_inicio_override,
                hora_fin_override=data.hora_fin_override,
                observaciones=data.observaciones,
                activo=data.activo,
            )
            self._container.calendario_personal_repo.create(bloque)

        self._refresh()

    def _on_eliminar(self) -> None:
        bloque_id = self._selected_id()
        if not bloque_id:
            return

        if QMessageBox.question(self, "Turnos", "¿Eliminar bloque?") != QMessageBox.Yes:
            return

        if self.cbo_tipo.currentText() == "Médico":
            self._container.calendario_medico_repo.delete(bloque_id)
        else:
            self._container.calendario_personal_repo.delete(bloque_id)

        self._refresh()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def _select_persona(self) -> None:
        if self.cbo_tipo.currentText() == "Médico":
            selection = select_medico(self, self._container.connection)
        else:
            selection = select_personal(self, self._container.connection)
        if not selection:
            return
        self._persona_id = selection.entity_id
        self.txt_persona.setText(selection.display)
        self._refresh()

    def _reset_persona(self) -> None:
        self._persona_id = None
        self.txt_persona.clear()
        self.table.setRowCount(0)

    def _open_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        menu = QMenu(self)
        action_new = menu.addAction("Añadir bloque")
        action_delete = menu.addAction("Eliminar bloque")
        action_delete.setEnabled(self._selected_id() is not None)
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == action_new:
            self._on_nuevo()
        elif action == action_delete:
            self._on_eliminar()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)
