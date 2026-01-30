from __future__ import annotations

from typing import Optional

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
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.pages.dialog_override import OverrideDialog
from clinicdesk.app.pages.materiales.dialogs.ajuste_stock import AjusteStockDialog
from clinicdesk.app.pages.materiales.dialogs.material_form import MaterialFormDialog
from clinicdesk.app.queries.materiales_queries import (
    MaterialesQueries,
    MaterialRow,
    MovimientoMaterialRow,
)
from clinicdesk.app.application.usecases.ajustar_stock_material import (
    AjustarStockMaterialRequest,
    AjustarStockMaterialUseCase,
    PendingWarningsError,
)
from clinicdesk.app.ui.error_presenter import present_error


class PageMateriales(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = MaterialesQueries(container.connection)

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
            ["ID", "Nombre", "Stock", "Fungible", "Activo"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        self.table_movs = QTableWidget(0, 5)
        self.table_movs.setHorizontalHeaderLabels(
            ["Fecha", "Tipo", "Cantidad", "Personal", "Motivo"]
        )
        self.table_movs.horizontalHeader().setStretchLastSection(True)

        root.addLayout(filters)
        root.addLayout(actions)
        root.addWidget(QLabel("Materiales"))
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
        rows = self._queries.search(texto=self.txt_buscar.text().strip() or None, activo=activo)
        self._render(rows)
        self._render_movimientos([])

    def _render(self, rows: list[MaterialRow]) -> None:
        self.table.setRowCount(0)
        for m in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(m.id)))
            self.table.setItem(row, 1, QTableWidgetItem(m.nombre))
            self.table.setItem(row, 2, QTableWidgetItem(str(m.stock)))
            self.table.setItem(row, 3, QTableWidgetItem("Sí" if m.fungible else "No"))
            self.table.setItem(row, 4, QTableWidgetItem("Sí" if m.activo else "No"))

    def _render_movimientos(self, rows: list[MovimientoMaterialRow]) -> None:
        self.table_movs.setRowCount(0)
        for m in rows:
            row = self.table_movs.rowCount()
            self.table_movs.insertRow(row)
            self.table_movs.setItem(row, 0, QTableWidgetItem(m.fecha_hora))
            self.table_movs.setItem(row, 1, QTableWidgetItem(m.tipo))
            self.table_movs.setItem(row, 2, QTableWidgetItem(str(m.cantidad)))
            self.table_movs.setItem(row, 3, QTableWidgetItem(m.personal))
            self.table_movs.setItem(row, 4, QTableWidgetItem(m.motivo))

    def _on_selection_changed(self) -> None:
        has_selection = self._selected_id() is not None
        self.btn_editar.setEnabled(has_selection)
        self.btn_desactivar.setEnabled(has_selection)
        self.btn_ajustar.setEnabled(has_selection)
        if has_selection:
            self._load_movimientos()

    def _load_movimientos(self) -> None:
        material_id = self._selected_id()
        if not material_id:
            return
        rows = self._queries.list_movimientos(material_id)
        self._render_movimientos(rows)

    def _on_nuevo(self) -> None:
        dialog = MaterialFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.materiales_repo.create(data.material)
        except ValidationError as exc:
            present_error(self, exc)
            return
        self._reset_filters()
        self._refresh()

    def _on_editar(self) -> None:
        material_id = self._selected_id()
        if not material_id:
            return
        material = self._container.materiales_repo.get_by_id(material_id)
        if not material:
            return
        dialog = MaterialFormDialog(self)
        dialog.set_material(material)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        try:
            self._container.materiales_repo.update(data.material)
        except ValidationError as exc:
            present_error(self, exc)
            return
        self._refresh()

    def _on_desactivar(self) -> None:
        material_id = self._selected_id()
        if not material_id:
            return
        if QMessageBox.question(self, "Materiales", "¿Desactivar material?") != QMessageBox.Yes:
            return
        self._container.materiales_repo.delete(material_id)
        self._refresh()

    def _on_ajustar_stock(self) -> None:
        material_id = self._selected_id()
        if not material_id:
            return
        dialog = AjusteStockDialog(self, container=self._container)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return

        req = AjustarStockMaterialRequest(
            material_id=material_id,
            tipo=data.tipo,
            cantidad=data.cantidad,
            personal_id=data.personal_id,
            motivo=data.motivo,
        )

        try:
            AjustarStockMaterialUseCase(self._container).execute(req)
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
            AjustarStockMaterialUseCase(self._container).execute(req)
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
    print("Este módulo no se ejecuta directamente. Usa: python -m clinicdesk")
    raise SystemExit(2)
