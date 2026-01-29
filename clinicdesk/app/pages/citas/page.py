from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.queries.citas_queries import CitaRow, CitasQueries
from clinicdesk.app.application.usecases.crear_cita import CrearCitaUseCase


class PageCitas(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = CitasQueries(container)

        self.calendar = QCalendarWidget()
        self.lbl_date = QLabel("Fecha: —")

        self.btn_new = QPushButton("Nueva cita")
        self.btn_delete = QPushButton("Eliminar cita")

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Inicio", "Fin", "Paciente", "Médico", "Sala", "Estado", "Motivo", "Paciente ID"]
        )
        self.table.setColumnHidden(8, True)

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
            self.table.setItem(r, 8, QTableWidgetItem(str(c.paciente_id)))


if __name__ == "__main__":
    print("Este módulo no se ejecuta directamente. Usa: python -m clinicdesk")
    raise SystemExit(2)
