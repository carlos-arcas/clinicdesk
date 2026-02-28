from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
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
from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget
from clinicdesk.app.pages.shared.crud_page_helpers import confirm_deactivation, set_buttons_enabled
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
from clinicdesk.app.pages.shared.screen_data_log import log_screen_data_loaded
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest


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

        self.filtros = FiltroListadoWidget(self)

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
        self.lbl_empty = QLabel("No hay datos cargados. Pulsa ‘Generar datos demo’.")
        self.btn_seed_demo = QPushButton("Generar datos demo")
        self.lbl_empty.setVisible(False)
        self.btn_seed_demo.setVisible(False)

        root.addWidget(self.filtros)
        root.addLayout(actions)
        root.addWidget(QLabel("Medicamentos"))
        root.addWidget(self.table)
        root.addWidget(QLabel("Movimientos"))
        root.addWidget(self.table_movs)
        root.addWidget(self.lbl_empty)
        root.addWidget(self.btn_seed_demo)

    def _connect_signals(self) -> None:
        self.filtros.filtros_cambiados.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.itemDoubleClicked.connect(lambda _: self._on_editar())
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_editar.clicked.connect(self._on_editar)
        self.btn_desactivar.clicked.connect(self._on_desactivar)
        self.btn_ajustar.clicked.connect(self._on_ajustar_stock)
        self.btn_seed_demo.clicked.connect(self._on_seed_demo)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        activo = self.filtros.activo()
        base_rows = self._queries.list_all(activo=activo)
        texto = normalize_search_text(self.filtros.texto())
        if not has_search_values(texto):
            rows = base_rows
        else:
            rows = self._queries.search(texto=texto, activo=activo)
        self.filtros.set_contador(len(rows), len(base_rows))
        self._render(rows)
        self._render_movimientos([])
        self._update_buttons()
        log_screen_data_loaded(self._container.connection, "medicamentos", len(rows))
        has_data = bool(rows)
        self.lbl_empty.setVisible(not has_data)
        self.btn_seed_demo.setVisible(not has_data)

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

    def _update_buttons(self) -> None:
        has_selection = self._selected_id() is not None
        set_buttons_enabled(
            has_selection=has_selection,
            buttons=[self.btn_editar, self.btn_desactivar, self.btn_ajustar],
        )
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
        if not confirm_deactivation(self, module_title="Medicamentos", entity_label="medicamento"):
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

    def _on_seed_demo(self) -> None:
        self._container.demo_ml_facade.seed_demo(SeedDemoDataRequest())
        self._refresh()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)
