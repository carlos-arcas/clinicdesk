from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.pages.medicos.dialogs.medico_form import MedicoFormDialog
from clinicdesk.app.queries.medicos_queries import MedicosQueries, MedicoRow


class PageMedicos(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = MedicosQueries(container.connection)

        self._build_ui()
        self._connect_signals()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_especialidad = QLineEdit()
        self.cbo_activo = QComboBox()
        self.cbo_activo.addItems(["Activos", "Inactivos", "Todos"])
        self.btn_buscar = QPushButton("Buscar")

        filters.addWidget(QLabel("Buscar"))
        filters.addWidget(self.txt_buscar)
        filters.addWidget(QLabel("Especialidad"))
        filters.addWidget(self.txt_especialidad)
        filters.addWidget(QLabel("Estado"))
        filters.addWidget(self.cbo_activo)
        filters.addWidget(self.btn_buscar)

        actions = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_editar = QPushButton("Editar")
        self.btn_desactivar = QPushButton("Desactivar")
        self.btn_editar.setEnabled(False)
        self.btn_desactivar.setEnabled(False)
        actions.addWidget(self.btn_nuevo)
        actions.addWidget(self.btn_editar)
        actions.addWidget(self.btn_desactivar)
        actions.addStretch(1)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Documento", "Nombre", "Teléfono", "Especialidad", "Activo"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addLayout(filters)
        root.addLayout(actions)
        root.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.btn_buscar.clicked.connect(self._refresh)
        self.txt_buscar.returnPressed.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_editar.clicked.connect(self._on_editar)
        self.btn_desactivar.clicked.connect(self._on_desactivar)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        activo = self._activo_filter()
        rows = self._queries.search(
            texto=self.txt_buscar.text().strip() or None,
            especialidad=self.txt_especialidad.text().strip() or None,
            activo=activo,
        )
        self._render(rows)

    def _render(self, rows: list[MedicoRow]) -> None:
        self.table.setRowCount(0)
        for m in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(m.id)))
            self.table.setItem(row, 1, QTableWidgetItem(m.documento))
            self.table.setItem(row, 2, QTableWidgetItem(m.nombre_completo))
            self.table.setItem(row, 3, QTableWidgetItem(m.telefono))
            self.table.setItem(row, 4, QTableWidgetItem(m.especialidad))
            self.table.setItem(row, 5, QTableWidgetItem("Sí" if m.activo else "No"))

    def _on_selection_changed(self) -> None:
        has_selection = self._selected_id() is not None
        self.btn_editar.setEnabled(has_selection)
        self.btn_desactivar.setEnabled(has_selection)

    def _on_nuevo(self) -> None:
        dialog = MedicoFormDialog(self)
        if dialog.exec() != dialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.medicos_repo.create(data.medico)
        except ValidationError as exc:
            QMessageBox.warning(self, "Médicos", str(exc))
            return
        self._reset_filters()
        self._refresh()

    def _on_editar(self) -> None:
        medico_id = self._selected_id()
        if not medico_id:
            return
        medico = self._container.medicos_repo.get_by_id(medico_id)
        if not medico:
            return
        dialog = MedicoFormDialog(self)
        dialog.set_medico(medico)
        if dialog.exec() != dialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.medicos_repo.update(data.medico)
        except ValidationError as exc:
            QMessageBox.warning(self, "Médicos", str(exc))
            return
        self._refresh()

    def _on_desactivar(self) -> None:
        medico_id = self._selected_id()
        if not medico_id:
            return
        if QMessageBox.question(self, "Médicos", "¿Desactivar médico?") != QMessageBox.Yes:
            return
        self._container.medicos_repo.delete(medico_id)
        self._refresh()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def _activo_filter(self) -> Optional[bool]:
        value = self.cbo_activo.currentText()
        if value == "Activos":
            return True
        if value == "Inactivos":
            return False
        return None

    def _reset_filters(self) -> None:
        self.txt_buscar.clear()
        self.txt_especialidad.clear()
        self.cbo_activo.setCurrentText("Todos")
