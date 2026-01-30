from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.controllers.citas_controller import CitasController
from clinicdesk.app.queries.citas_queries import CitaRow, CitasQueries


class PageCitas(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = CitasQueries(container)
        self._controller = CitasController(self, container)

        self.calendar = QCalendarWidget()
        self.lbl_date = QLabel("Fecha: —")

        self.btn_new = QPushButton("Nueva cita")
        self.btn_delete = QPushButton("Eliminar cita")
        self.btn_delete.setEnabled(False)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Inicio", "Fin", "Paciente", "Médico", "Sala", "Estado", "Motivo"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        left = QVBoxLayout()
        left.addWidget(self.calendar)
        left.addWidget(self.lbl_date)
        left.addWidget(self.btn_new)
        left.addWidget(self.btn_delete)

        right = QVBoxLayout()
        right.addWidget(self.table)

        root = QHBoxLayout(self)
        root.addLayout(left, 1)
        root.addLayout(right, 3)

        self.calendar.selectionChanged.connect(self._refresh)
        self.btn_new.clicked.connect(self._on_new)
        self.btn_delete.clicked.connect(self._on_delete)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.customContextMenuRequested.connect(self._open_context_menu)

        self._refresh()

    def on_show(self):
        self._refresh()

    def _refresh(self):
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
            self.table.setItem(r, 6, QTableWidgetItem(c.estado))
            self.table.setItem(r, 7, QTableWidgetItem(c.motivo or ""))

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def _on_selection_changed(self) -> None:
        self.btn_delete.setEnabled(self._selected_id() is not None)

    def _on_new(self) -> None:
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        if self._controller.create_cita_flow(date_str):
            self._refresh()

    def _on_delete(self) -> None:
        cita_id = self._selected_id()
        if not cita_id:
            return
        if self._controller.delete_cita(cita_id):
            self._refresh()

    def _open_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        menu = QMenu(self)
        action_new = menu.addAction("Nueva cita")
        action_delete = menu.addAction("Eliminar cita")
        action_delete.setEnabled(self._selected_id() is not None)
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == action_new:
            self._on_new()
        elif action == action_delete:
            self._on_delete()


if __name__ == "__main__":
    print("Este módulo no se ejecuta directamente. Usa: python -m clinicdesk")
    raise SystemExit(2)
