from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtCore import Qt
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
    QDialog,
    QMenu,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.common.search_utils import has_search_values, normalize_search_text
from clinicdesk.app.pages.medicos.dialogs.medico_form import MedicoFormDialog
from clinicdesk.app.pages.shared.table_utils import apply_row_style, set_item
from clinicdesk.app.queries.medicos_queries import MedicosQueries, MedicoRow
from clinicdesk.app.ui.error_presenter import present_error


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
        self.btn_csv = QPushButton("Importar/Exportar CSV…")
        self.btn_editar.setEnabled(False)
        self.btn_desactivar.setEnabled(False)
        actions.addWidget(self.btn_nuevo)
        actions.addWidget(self.btn_editar)
        actions.addWidget(self.btn_desactivar)
        actions.addWidget(self.btn_csv)
        actions.addStretch(1)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Documento", "Nombre", "Teléfono", "Especialidad", "Activo"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        root.addLayout(filters)
        root.addLayout(actions)
        root.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.btn_buscar.clicked.connect(self._refresh)
        self.txt_buscar.returnPressed.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_editar.clicked.connect(self._on_editar)
        self.btn_desactivar.clicked.connect(self._on_desactivar)
        self.btn_csv.clicked.connect(self._open_csv_dialog)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        selected_id = self._selected_id()
        activo = self._activo_filter()
        texto = normalize_search_text(self.txt_buscar.text())
        especialidad = normalize_search_text(self.txt_especialidad.text())
        if not has_search_values(texto, especialidad):
            rows = self._queries.list_all(activo=activo)
        else:
            rows = self._queries.search(
                texto=texto,
                especialidad=especialidad,
                activo=activo,
            )
        self._render(rows)
        if selected_id is not None:
            self._select_by_id(selected_id)

    def _render(self, rows: list[MedicoRow]) -> None:
        self.table.setRowCount(0)
        for m in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            set_item(self.table, row, 0, str(m.id))
            set_item(self.table, row, 1, m.documento)
            set_item(self.table, row, 2, m.nombre_completo)
            set_item(self.table, row, 3, m.telefono)
            set_item(self.table, row, 4, m.especialidad)
            set_item(self.table, row, 5, "Sí" if m.activo else "No")
            tooltip = (
                f"Documento: {m.documento}\n"
                f"Teléfono: {m.telefono or '—'}\n"
                f"Especialidad: {m.especialidad}\n"
                f"Estado: {'Activo' if m.activo else 'Inactivo'}"
            )
            apply_row_style(self.table, row, inactive=not m.activo, tooltip=tooltip)

    def _on_selection_changed(self) -> None:
        has_selection = self._selected_id() is not None
        self.btn_editar.setEnabled(has_selection)
        self.btn_desactivar.setEnabled(has_selection)

    def _on_nuevo(self) -> None:
        dialog = MedicoFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.medicos_repo.create(data.medico)
        except Exception as exc:
            context = (
                f"Tipo documento: {data.medico.tipo_documento.value}\n"
                f"Documento: {data.medico.documento}"
            )
            present_error(self, exc, context=context)
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
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.medicos_repo.update(data.medico)
        except Exception as exc:
            context = (
                f"Tipo documento: {data.medico.tipo_documento.value}\n"
                f"Documento: {data.medico.documento}"
            )
            present_error(self, exc, context=context)
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

    def _select_by_id(self, medico_id: int) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == str(medico_id):
                self.table.setCurrentCell(row, 0)
                return

    def _open_csv_dialog(self) -> None:
        window = self.window()
        open_dialog = getattr(window, "open_csv_dialog", None)
        if callable(open_dialog):
            open_dialog()
            return
        QMessageBox.information(
            self,
            "CSV",
            "Esta acción está disponible en la ventana principal. "
            "Ejecuta la aplicación con: python -m clinicdesk",
        )

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

    def _open_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        menu = QMenu(self)
        action_new = menu.addAction("Nuevo")
        action_edit = menu.addAction("Editar")
        action_delete = menu.addAction("Desactivar")
        has_selection = self._selected_id() is not None
        action_edit.setEnabled(has_selection)
        action_delete.setEnabled(has_selection)
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == action_new:
            self._on_nuevo()
        elif action == action_edit:
            self._on_editar()
        elif action == action_delete:
            self._on_desactivar()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)
