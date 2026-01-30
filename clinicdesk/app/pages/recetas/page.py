from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
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
from clinicdesk.app.queries.pacientes_queries import PacientesQueries, PacienteRow
from clinicdesk.app.queries.recetas_queries import RecetasQueries, RecetaRow, RecetaLineaRow


class PageRecetas(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._pacientes_queries = PacientesQueries(container.connection)
        self._recetas_queries = RecetasQueries(container.connection)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.btn_buscar = QPushButton("Buscar pacientes")

        top.addWidget(QLabel("Buscar"))
        top.addWidget(self.txt_buscar)
        top.addWidget(self.btn_buscar)

        self.table_pacientes = QTableWidget(0, 3)
        self.table_pacientes.setHorizontalHeaderLabels(["ID", "Documento", "Nombre"])
        self.table_pacientes.setColumnHidden(0, True)
        self.table_pacientes.horizontalHeader().setStretchLastSection(True)

        self.table_recetas = QTableWidget(0, 4)
        self.table_recetas.setHorizontalHeaderLabels(["ID", "Fecha", "Médico", "Estado"])
        self.table_recetas.setColumnHidden(0, True)
        self.table_recetas.horizontalHeader().setStretchLastSection(True)

        self.table_lineas = QTableWidget(0, 6)
        self.table_lineas.setHorizontalHeaderLabels(
            ["ID", "Medicamento", "Dosis", "Cantidad", "Pendiente", "Estado"]
        )
        self.table_lineas.setColumnHidden(0, True)
        self.table_lineas.horizontalHeader().setStretchLastSection(True)

        root.addLayout(top)
        root.addWidget(QLabel("Pacientes"))
        root.addWidget(self.table_pacientes)
        root.addWidget(QLabel("Recetas"))
        root.addWidget(self.table_recetas)
        root.addWidget(QLabel("Líneas"))
        root.addWidget(self.table_lineas)

    def _connect_signals(self) -> None:
        self.btn_buscar.clicked.connect(self._buscar_pacientes)
        self.table_pacientes.itemSelectionChanged.connect(self._select_paciente)
        self.table_recetas.itemSelectionChanged.connect(self._cargar_lineas)

    def on_show(self) -> None:
        self._buscar_pacientes()

    def _buscar_pacientes(self) -> None:
        texto = self.txt_buscar.text().strip() or None
        rows = self._pacientes_queries.search(texto=texto, activo=None)
        self._render_pacientes(rows)

    def _render_pacientes(self, rows: list[PacienteRow]) -> None:
        self.table_pacientes.setRowCount(0)
        for p in rows:
            row = self.table_pacientes.rowCount()
            self.table_pacientes.insertRow(row)
            self.table_pacientes.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.table_pacientes.setItem(row, 1, QTableWidgetItem(p.documento))
            self.table_pacientes.setItem(row, 2, QTableWidgetItem(p.nombre_completo))

    def _select_paciente(self) -> None:
        paciente_id = self._selected_id(self.table_pacientes)
        if paciente_id:
            self._cargar_recetas()

    def _cargar_recetas(self) -> None:
        paciente_id = self._selected_id(self.table_pacientes)
        if not paciente_id:
            return
        rows = self._recetas_queries.list_por_paciente(paciente_id)
        self._render_recetas(rows)
        self._render_lineas([])

    def _render_recetas(self, rows: list[RecetaRow]) -> None:
        self.table_recetas.setRowCount(0)
        for r in rows:
            row = self.table_recetas.rowCount()
            self.table_recetas.insertRow(row)
            self.table_recetas.setItem(row, 0, QTableWidgetItem(str(r.id)))
            self.table_recetas.setItem(row, 1, QTableWidgetItem(r.fecha))
            self.table_recetas.setItem(row, 2, QTableWidgetItem(r.medico))
            self.table_recetas.setItem(row, 3, QTableWidgetItem(r.estado))

    def _cargar_lineas(self) -> None:
        receta_id = self._selected_id(self.table_recetas)
        if not receta_id:
            return
        rows = self._recetas_queries.list_lineas(receta_id)
        self._render_lineas(rows)

    def _render_lineas(self, rows: list[RecetaLineaRow]) -> None:
        self.table_lineas.setRowCount(0)
        for l in rows:
            row = self.table_lineas.rowCount()
            self.table_lineas.insertRow(row)
            self.table_lineas.setItem(row, 0, QTableWidgetItem(str(l.id)))
            self.table_lineas.setItem(row, 1, QTableWidgetItem(l.medicamento))
            self.table_lineas.setItem(row, 2, QTableWidgetItem(l.dosis))
            self.table_lineas.setItem(row, 3, QTableWidgetItem(str(l.cantidad)))
            self.table_lineas.setItem(row, 4, QTableWidgetItem(str(l.pendiente)))
            self.table_lineas.setItem(row, 5, QTableWidgetItem(l.estado))

    def _selected_id(self, table: QTableWidget) -> Optional[int]:
        items = table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None




if __name__ == "__main__":
    print("Este módulo no se ejecuta directamente. Usa: python -m clinicdesk")
    raise SystemExit(2)
