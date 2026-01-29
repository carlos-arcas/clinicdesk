from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.queries.dispensaciones_queries import DispensacionesQueries, DispensacionRow


class PageDispensaciones(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = DispensacionesQueries(container.connection)

        self._build_ui()
        self._connect_signals()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addMonths(-1))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.txt_paciente_id = QLineEdit()
        self.txt_personal_id = QLineEdit()
        self.txt_medicamento_id = QLineEdit()
        self.btn_filtrar = QPushButton("Filtrar")

        filters.addWidget(QLabel("Desde"))
        filters.addWidget(self.date_desde)
        filters.addWidget(QLabel("Hasta"))
        filters.addWidget(self.date_hasta)
        filters.addWidget(QLabel("Paciente ID"))
        filters.addWidget(self.txt_paciente_id)
        filters.addWidget(QLabel("Personal ID"))
        filters.addWidget(self.txt_personal_id)
        filters.addWidget(QLabel("Medicamento ID"))
        filters.addWidget(self.txt_medicamento_id)
        filters.addWidget(self.btn_filtrar)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Fecha",
                "Paciente",
                "Personal",
                "Medicamento",
                "Cantidad",
                "Receta",
                "Incidencia",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addLayout(filters)
        root.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.btn_filtrar.clicked.connect(self._refresh)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        fecha_desde = self.date_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = self.date_hasta.date().toString("yyyy-MM-dd")
        rows = self._queries.list(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            paciente_id=self._int_or_none(self.txt_paciente_id.text().strip()),
            personal_id=self._int_or_none(self.txt_personal_id.text().strip()),
            medicamento_id=self._int_or_none(self.txt_medicamento_id.text().strip()),
        )
        self._render(rows)

    def _render(self, rows: list[DispensacionRow]) -> None:
        self.table.setRowCount(0)
        for d in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(d.id)))
            self.table.setItem(row, 1, QTableWidgetItem(d.fecha_hora))
            self.table.setItem(row, 2, QTableWidgetItem(d.paciente))
            self.table.setItem(row, 3, QTableWidgetItem(d.personal))
            self.table.setItem(row, 4, QTableWidgetItem(d.medicamento))
            self.table.setItem(row, 5, QTableWidgetItem(str(d.cantidad)))
            self.table.setItem(row, 6, QTableWidgetItem(str(d.receta_id)))
            self.table.setItem(row, 7, QTableWidgetItem("Sí" if d.incidencia else "No"))

    @staticmethod
    def _int_or_none(value: str) -> Optional[int]:
        if not value:
            return None
        try:
            number = int(value)
            return number if number > 0 else None
        except ValueError:
            return None


if __name__ == "__main__":
    print("Este módulo no se ejecuta directamente. Usa: python -m clinicdesk")
    raise SystemExit(2)
