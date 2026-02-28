from __future__ import annotations

from typing import Optional

import logging

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
from clinicdesk.app.pages.shared.screen_data_log import log_screen_data_loaded
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest


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
        self.txt_paciente = QLineEdit()
        self.txt_personal = QLineEdit()
        self.txt_medicamento = QLineEdit()
        self.btn_filtrar = QPushButton("Filtrar")

        filters.addWidget(QLabel("Desde"))
        filters.addWidget(self.date_desde)
        filters.addWidget(QLabel("Hasta"))
        filters.addWidget(self.date_hasta)
        filters.addWidget(QLabel("Paciente"))
        filters.addWidget(self.txt_paciente)
        filters.addWidget(QLabel("Personal"))
        filters.addWidget(self.txt_personal)
        filters.addWidget(QLabel("Medicamento"))
        filters.addWidget(self.txt_medicamento)
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
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(6, True)
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addLayout(filters)
        root.addWidget(self.table)
        self.lbl_empty = QLabel("No hay datos cargados. Pulsa ‘Generar datos demo’.")
        self.btn_seed_demo = QPushButton("Generar datos demo")
        self.lbl_empty.setVisible(False)
        self.btn_seed_demo.setVisible(False)
        root.addWidget(self.lbl_empty)
        root.addWidget(self.btn_seed_demo)

    def _connect_signals(self) -> None:
        self.btn_filtrar.clicked.connect(self._refresh)
        self.btn_seed_demo.clicked.connect(self._on_seed_demo)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        fecha_desde = self.date_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = self.date_hasta.date().toString("yyyy-MM-dd")
        rows = self._queries.list(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            paciente_texto=self.txt_paciente.text().strip() or None,
            personal_texto=self.txt_personal.text().strip() or None,
            medicamento_texto=self.txt_medicamento.text().strip() or None,
        )
        self._render(rows)
        log_screen_data_loaded(self._container.connection, "dispensaciones", len(rows))
        self.lbl_empty.setVisible(not bool(rows))
        self.btn_seed_demo.setVisible(not bool(rows))

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

    def _on_seed_demo(self) -> None:
        self._container.demo_ml_facade.seed_demo(SeedDemoDataRequest())
        self._refresh()




if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)
