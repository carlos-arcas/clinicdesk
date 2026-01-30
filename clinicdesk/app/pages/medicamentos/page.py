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
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.pages.dialog_override import OverrideDialog
from clinicdesk.app.pages.medicamentos.dialogs.ajuste_stock import AjusteStockDialog
from clinicdesk.app.pages.medicamentos.dialogs.medicamento_form import MedicamentoFormDialog
from clinicdesk.app.pages.shared.table_utils import apply_row_style, set_item
from clinicdesk.app.queries.medicamentos_queries import (
    MedicamentosQueries,
    MedicamentoRow,
    MovimientoMedicamentoRow,
)
from clinicdesk.app.application.usecases.ajustar_stock_medicamento import (
    AjustarStockMedicamentoRequest,
    AjustarStockMedicamentoUseCase,
    PendingWarningsError,
)
from clinicdesk.app.ui.error_presenter import present_error


class PageMedicamentos(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = MedicamentosQueries(container.connection)

        self._build_ui()
        self._connect_signals()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.cbo_activo = QComboBox()
        self.cbo_activo.addItems(["Activos", "Inactivos", "Todos"])
        self.btn_buscar = QPushButton("Buscar")

        filters.addWidget(QLabel("Buscar"))
        filters.addWidget(self.txt_buscar)
        filters.addWidget(QLabel("Estado"))
        filters.addWidget(self.cbo_activo)
        filters.addWidget(self.btn_buscar)

        actions = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_editar = QPushButton("Editar")
        self.btn_desactivar = QPushButton("Desactivar")
        self.btn_ajustar = QPushButton("Ajustar stock")
        self.btn_editar.setEnabled(False)
        self.btn_desactivar.setEnabled(False)
        self.btn_ajustar.setEnabled(False)
        actions.addWidget(self.btn_nuevo)
        actions.addWidget(self.btn_editar)
        actions.addWidget(self.btn_desactivar)
        actions.addWidget(self.btn_ajustar)
        actions.addStretch(1)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre comercial", "Nombre compuesto", "Stock", "Activo"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        self.table_movs = QTableWidget(0, 6)
        self.table_movs.setHorizontalHeaderLabels(
            ["Fecha", "Tipo", "Cantidad", "Personal", "Motivo", "Referencia"]
        )
        self.table_movs.horizontalHeader().setStretchLastSection(True)

        root.addLayout(filters)
        root.addLayout(actions)
        root.addWidget(QLabel("Medicamentos"))
        root.addWidget(self.table)
        root.addWidget(QLabel("Movimientos"))
        root.addWidget(self.table_movs)

    def _connect_signals(self) -> None:
        self.btn_buscar.clicked.connect(self._refresh)
        self.txt_buscar.returnPressed.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_editar.clicked.connect(self._on_editar)
        self.btn_desactivar.clicked.connect(self._on_desactivar)
        self.btn_ajustar.clicked.connect(self._on_ajustar_stock)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        activo = self._activo_filter()
        texto = normalize_search_text(self.txt_buscar.text())
        if not has_search_values(texto):
            rows = self._queries.list_all(activo=activo)
        else:
            rows = self._queries.search(texto=texto, activo=activo)
        self._render(rows)
        self._render_movimientos([])

    def _render(self, rows: list[MedicamentoRow]) -> None:
        self.table.setRowCount(0)
        for m in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            set_item(self.table, row, 0, str(m.id))
            set_item(self.table, row, 1, m.nombre_comercial)
            set_item(self.table, row, 2, m.nombre_compuesto)
            set_item(self.table, row, 3, str(m.stock))
            set_item(self.table, row, 4, "Sí" if m.activo else "No")
            tooltip = (
                f"Comercial: {m.nombre_comercial}\n"
                f"Compuesto: {m.nombre_compuesto}\n"
                f"Stock: {m.stock}\n"
                f"Estado: {'Activo' if m.activo else 'Inactivo'}"
            )
            apply_row_style(self.table, row, inactive=not m.activo, tooltip=tooltip)

    def _render_movimientos(self, rows: list[MovimientoMedicamentoRow]) -> None:
        self.table_movs.setRowCount(0)
        for m in rows:
            row = self.table_movs.rowCount()
            self.table_movs.insertRow(row)
            self.table_movs.setItem(row, 0, QTableWidgetItem(m.fecha_hora))
            self.table_movs.setItem(row, 1, QTableWidgetItem(m.tipo))
            self.table_movs.setItem(row, 2, QTableWidgetItem(str(m.cantidad)))
            self.table_movs.setItem(row, 3, QTableWidgetItem(m.personal))
            self.table_movs.setItem(row, 4, QTableWidgetItem(m.motivo))
            self.table_movs.setItem(row, 5, QTableWidgetItem(m.referencia))

    def _on_selection_changed(self) -> None:
        has_selection = self._selected_id() is not None
        self.btn_editar.setEnabled(has_selection)
        self.btn_desactivar.setEnabled(has_selection)
        self.btn_ajustar.setEnabled(has_selection)
        if has_selection:
            self._load_movimientos()

    def _load_movimientos(self) -> None:
        medicamento_id = self._selected_id()
        if not medicamento_id:
            return
        rows = self._queries.list_movimientos(medicamento_id)
        self._render_movimientos(rows)

    def _on_nuevo(self) -> None:
        dialog = MedicamentoFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.medicamentos_repo.create(data.medicamento)
        except ValidationError as exc:
            present_error(self, exc)
            return
        self._reset_filters()
        self._refresh()

    def _on_editar(self) -> None:
        medicamento_id = self._selected_id()
        if not medicamento_id:
            return
        medicamento = self._container.medicamentos_repo.get_by_id(medicamento_id)
        if not medicamento:
            return
        dialog = MedicamentoFormDialog(self)
        dialog.set_medicamento(medicamento)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.medicamentos_repo.update(data.medicamento)
        except ValidationError as exc:
            present_error(self, exc)
            return
        self._refresh()

    def _on_desactivar(self) -> None:
        medicamento_id = self._selected_id()
        if not medicamento_id:
            return
        if QMessageBox.question(self, "Medicamentos", "¿Desactivar medicamento?") != QMessageBox.Yes:
            return
        self._container.medicamentos_repo.delete(medicamento_id)
        self._refresh()

    def _on_ajustar_stock(self) -> None:
        medicamento_id = self._selected_id()
        if not medicamento_id:
            return
        dialog = AjusteStockDialog(self, container=self._container)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return

        req = AjustarStockMedicamentoRequest(
            medicamento_id=medicamento_id,
            tipo=data.tipo,
            cantidad=data.cantidad,
            personal_id=data.personal_id,
            motivo=data.motivo,
            referencia=data.referencia,
        )

        try:
            AjustarStockMedicamentoUseCase(self._container).execute(req)
        except PendingWarningsError as warn:
            override = OverrideDialog(
                self,
                title="Confirmar ajuste con advertencias",
                warnings=warn.warnings,
                container=self._container,
            )
            if override.exec() != QDialog.Accepted:
                return
            decision = override.get_decision()
            if not decision.accepted:
                return
            req.override = True
            req.nota_override = decision.nota_override
            req.confirmado_por_personal_id = decision.confirmado_por_personal_id
            AjustarStockMedicamentoUseCase(self._container).execute(req)
        except ValidationError as exc:
            present_error(self, exc)
            return

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
        self.cbo_activo.setCurrentText("Todos")

    def _open_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        menu = QMenu(self)
        action_new = menu.addAction("Nuevo")
        action_edit = menu.addAction("Editar")
        action_delete = menu.addAction("Desactivar")
        action_adjust = menu.addAction("Ajustar stock")
        has_selection = self._selected_id() is not None
        action_edit.setEnabled(has_selection)
        action_delete.setEnabled(has_selection)
        action_adjust.setEnabled(has_selection)
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == action_new:
            self._on_nuevo()
        elif action == action_edit:
            self._on_editar()
        elif action == action_delete:
            self._on_desactivar()
        elif action == action_adjust:
            self._on_ajustar_stock()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)
