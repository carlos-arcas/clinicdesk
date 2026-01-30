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
from clinicdesk.app.domain.enums import TipoSala
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.pages.salas.dialogs.sala_form import SalaFormDialog
from clinicdesk.app.pages.shared.table_utils import apply_row_style, set_item
from clinicdesk.app.queries.salas_queries import SalasQueries, SalaRow
from clinicdesk.app.ui.error_presenter import present_error


class PageSalas(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = SalasQueries(container.connection)

        self._build_ui()
        self._connect_signals()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.cbo_tipo = QComboBox()
        self.cbo_tipo.addItem("Todos")
        self.cbo_tipo.addItems([t.value for t in TipoSala])
        self.cbo_activa = QComboBox()
        self.cbo_activa.addItems(["Activas", "Inactivas", "Todas"])
        self.btn_buscar = QPushButton("Buscar")

        filters.addWidget(QLabel("Buscar"))
        filters.addWidget(self.txt_buscar)
        filters.addWidget(QLabel("Tipo"))
        filters.addWidget(self.cbo_tipo)
        filters.addWidget(QLabel("Estado"))
        filters.addWidget(self.cbo_activa)
        filters.addWidget(self.btn_buscar)

        actions = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nueva")
        self.btn_editar = QPushButton("Editar")
        self.btn_desactivar = QPushButton("Desactivar")
        self.btn_editar.setEnabled(False)
        self.btn_desactivar.setEnabled(False)
        actions.addWidget(self.btn_nuevo)
        actions.addWidget(self.btn_editar)
        actions.addWidget(self.btn_desactivar)
        actions.addStretch(1)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Tipo", "Ubicación", "Activa"]
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

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        tipo = self.cbo_tipo.currentText()
        tipo = None if tipo == "Todos" else tipo
        activa = self._activa_filter()
        rows = self._queries.search(
            texto=self.txt_buscar.text().strip() or None,
            tipo=tipo,
            activa=activa,
        )
        self._render(rows)

    def _render(self, rows: list[SalaRow]) -> None:
        self.table.setRowCount(0)
        for s in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            set_item(self.table, row, 0, str(s.id))
            set_item(self.table, row, 1, s.nombre)
            set_item(self.table, row, 2, s.tipo)
            set_item(self.table, row, 3, s.ubicacion)
            set_item(self.table, row, 4, "Sí" if s.activa else "No")
            tooltip = (
                f"Sala: {s.nombre}\n"
                f"Tipo: {s.tipo}\n"
                f"Ubicación: {s.ubicacion or '—'}\n"
                f"Estado: {'Activa' if s.activa else 'Inactiva'}"
            )
            apply_row_style(self.table, row, inactive=not s.activa, tooltip=tooltip)

    def _on_selection_changed(self) -> None:
        has_selection = self._selected_id() is not None
        self.btn_editar.setEnabled(has_selection)
        self.btn_desactivar.setEnabled(has_selection)

    def _on_nuevo(self) -> None:
        dialog = SalaFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.salas_repo.create(data.sala)
        except ValidationError as exc:
            present_error(self, exc)
            return
        self._reset_filters()
        self._refresh()

    def _on_editar(self) -> None:
        sala_id = self._selected_id()
        if not sala_id:
            return
        sala = self._container.salas_repo.get_by_id(sala_id)
        if not sala:
            return
        dialog = SalaFormDialog(self)
        dialog.set_sala(sala)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.salas_repo.update(data.sala)
        except ValidationError as exc:
            present_error(self, exc)
            return
        self._refresh()

    def _on_desactivar(self) -> None:
        sala_id = self._selected_id()
        if not sala_id:
            return
        if QMessageBox.question(self, "Salas", "¿Desactivar sala?") != QMessageBox.Yes:
            return
        self._container.salas_repo.delete(sala_id)
        self._refresh()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def _activa_filter(self) -> Optional[bool]:
        value = self.cbo_activa.currentText()
        if value == "Activas":
            return True
        if value == "Inactivas":
            return False
        return None

    def _reset_filters(self) -> None:
        self.txt_buscar.clear()
        self.cbo_tipo.setCurrentText("Todos")
        self.cbo_activa.setCurrentText("Todas")

    def _open_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        menu = QMenu(self)
        action_new = menu.addAction("Nueva")
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
