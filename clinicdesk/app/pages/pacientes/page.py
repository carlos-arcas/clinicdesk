from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
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
from clinicdesk.app.application.usecases.pacientes_crud import (
    CrearPacienteUseCase,
    DesactivarPacienteUseCase,
    EditarPacienteUseCase,
)
from clinicdesk.app.common.search_utils import has_search_values, normalize_search_text
from clinicdesk.app.pages.pacientes.dialogs.paciente_form import PacienteFormDialog
from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget
from clinicdesk.app.pages.shared.crud_page_helpers import confirm_deactivation, set_buttons_enabled
from clinicdesk.app.pages.shared.table_utils import apply_row_style, set_item
from clinicdesk.app.queries.pacientes_queries import PacientesQueries, PacienteRow
from clinicdesk.app.ui.error_presenter import present_error


class PagePacientes(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = PacientesQueries(container.connection)
        self._can_write = container.user_context.can_write
        self._uc_crear = CrearPacienteUseCase(container.pacientes_repo, container.user_context)
        self._uc_editar = EditarPacienteUseCase(container.pacientes_repo, container.user_context)
        self._uc_desactivar = DesactivarPacienteUseCase(container.pacientes_repo, container.user_context)

        self._build_ui()
        self._connect_signals()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        self.filtros = FiltroListadoWidget(self)

        actions = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_editar = QPushButton("Editar")
        self.btn_desactivar = QPushButton("Desactivar")
        self.btn_csv = QPushButton("Importar/Exportar CSV…")
        self.btn_editar.setEnabled(False)
        self.btn_desactivar.setEnabled(False)
        self.btn_nuevo.setEnabled(self._can_write)
        actions.addWidget(self.btn_nuevo)
        actions.addWidget(self.btn_editar)
        actions.addWidget(self.btn_desactivar)
        actions.addWidget(self.btn_csv)
        actions.addStretch(1)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Documento", "Nombre", "Teléfono", "Activo"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        root.addWidget(self.filtros)
        root.addLayout(actions)
        root.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.filtros.filtros_cambiados.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.itemDoubleClicked.connect(lambda _: self._on_editar())
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_editar.clicked.connect(self._on_editar)
        self.btn_desactivar.clicked.connect(self._on_desactivar)
        self.btn_csv.clicked.connect(self._open_csv_dialog)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        selected_id = self._selected_id()
        activo = self.filtros.activo()
        base_rows = self._queries.list_all(activo=activo)
        texto = normalize_search_text(self.filtros.texto())
        if not has_search_values(texto):
            rows = base_rows
        else:
            rows = self._queries.search(texto=texto, activo=activo)
        self.filtros.set_contador(len(rows), len(base_rows))
        self._render(rows)
        if selected_id is not None:
            self._select_by_id(selected_id)
        self._update_buttons()

    def _render(self, rows: list[PacienteRow]) -> None:
        self.table.setRowCount(0)
        for p in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            set_item(self.table, row, 0, str(p.id))
            set_item(self.table, row, 1, p.documento)
            set_item(self.table, row, 2, p.nombre_completo)
            set_item(self.table, row, 3, p.telefono)
            set_item(self.table, row, 4, "Sí" if p.activo else "No")
            tooltip = (
                f"Documento: {p.documento}\n"
                f"Teléfono: {p.telefono or '—'}\n"
                f"Estado: {'Activo' if p.activo else 'Inactivo'}"
            )
            apply_row_style(self.table, row, inactive=not p.activo, tooltip=tooltip)

    def _update_buttons(self) -> None:
        if not self._can_write:
            self.btn_editar.setEnabled(False)
            self.btn_desactivar.setEnabled(False)
            return
        set_buttons_enabled(
            has_selection=self._selected_id() is not None,
            buttons=[self.btn_editar, self.btn_desactivar],
        )

    def _on_nuevo(self) -> None:
        dialog = PacienteFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._uc_crear.execute(data.paciente)
        except Exception as exc:
            context = (
                f"Tipo documento: {data.paciente.tipo_documento.value}\n"
                f"Documento: {data.paciente.documento}"
            )
            present_error(self, exc, context=context)
            return
        self._reset_filters()
        self._refresh()

    def _on_editar(self) -> None:
        paciente_id = self._selected_id()
        if not paciente_id:
            return
        paciente = self._container.pacientes_repo.get_by_id(paciente_id)
        if not paciente:
            return
        dialog = PacienteFormDialog(self)
        dialog.set_paciente(paciente)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._uc_editar.execute(data.paciente)
        except Exception as exc:
            context = (
                f"Tipo documento: {data.paciente.tipo_documento.value}\n"
                f"Documento: {data.paciente.documento}"
            )
            present_error(self, exc, context=context)
            return
        self._refresh()

    def _on_desactivar(self) -> None:
        paciente_id = self._selected_id()
        if not paciente_id:
            return
        if not confirm_deactivation(self, module_title="Pacientes", entity_label="paciente"):
            return
        self._uc_desactivar.execute(paciente_id)
        self._refresh()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def _select_by_id(self, paciente_id: int) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == str(paciente_id):
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

    def _reset_filters(self) -> None:
        self.filtros.limpiar()

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
        if not self._can_write:
            action_new.setEnabled(False)
            action_edit.setEnabled(False)
            action_delete.setEnabled(False)
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
