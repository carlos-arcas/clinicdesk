from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QDialog,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.dialog_dispensar import DispensarDialog
from clinicdesk.app.pages.dialog_override import OverrideDialog
from clinicdesk.app.pages.shared.selector_dialog import select_paciente
from clinicdesk.app.queries.farmacia_queries import (
    RecetaRow,
    RecetaLineaRow,
)
from clinicdesk.app.application.usecases.dispensar_medicamento import (
    DispensarMedicamentoRequest,
    DispensarMedicamentoUseCase,
    PendingWarningsError,
)
from clinicdesk.app.pages.shared.screen_data_log import log_screen_data_loaded
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest


class PageFarmacia(QWidget):
    """
    Página de Farmacia.

    UI pura:
    - Seleccionar paciente
    - Ver recetas
    - Ver líneas de receta
    - Dispensar medicamento
    """

    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._can_write = container.user_context.can_write
        self._paciente_id: Optional[int] = None

        self._build_ui()
        self._connect_signals()

    # ---------------- UI ----------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # Selección paciente
        top = QHBoxLayout()
        top.addWidget(QLabel("Paciente"))
        self.input_paciente = QLineEdit()
        self.input_paciente.setReadOnly(True)
        self.btn_buscar_paciente = QPushButton("Buscar…")
        self.btn_cargar = QPushButton("Cargar recetas")
        top.addWidget(self.input_paciente)
        top.addWidget(self.btn_buscar_paciente)
        top.addWidget(self.btn_cargar)

        # Tablas
        self.table_recetas = QTableWidget(0, 4)
        self.table_recetas.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Médico", "Estado"]
        )
        self.table_recetas.setColumnHidden(0, True)

        self.table_lineas = QTableWidget(0, 6)
        self.table_lineas.setHorizontalHeaderLabels(
            ["ID", "Medicamento", "Dosis", "Cantidad", "Pendiente", "Estado"]
        )
        self.table_lineas.setColumnHidden(0, True)

        self.btn_dispensar = QPushButton("Dispensar")
        self.btn_dispensar.setEnabled(False)
        self.lbl_empty = QLabel("No hay datos cargados. Pulsa ‘Generar datos demo’.")
        self.btn_seed_demo = QPushButton("Generar datos demo")
        self.lbl_empty.setVisible(False)
        self.btn_seed_demo.setVisible(False)

        root.addLayout(top)
        root.addWidget(QLabel("Recetas"))
        root.addWidget(self.table_recetas)
        root.addWidget(QLabel("Líneas de receta"))
        root.addWidget(self.table_lineas)
        root.addWidget(self.btn_dispensar)
        root.addWidget(self.lbl_empty)
        root.addWidget(self.btn_seed_demo)

    def _connect_signals(self) -> None:
        self.btn_buscar_paciente.clicked.connect(self._select_paciente)
        self.btn_cargar.clicked.connect(self._load_recetas)
        self.table_recetas.itemSelectionChanged.connect(self._load_lineas)
        self.table_lineas.itemSelectionChanged.connect(self._on_linea_selected)
        self.btn_dispensar.clicked.connect(self._on_dispensar)
        self.btn_seed_demo.clicked.connect(self._on_seed_demo)

    # ---------------- Actions ----------------

    def _load_recetas(self) -> None:
        paciente_id = self._paciente_id
        if not paciente_id:
            return

        recetas = self._container.queries.farmacia.recetas_por_paciente(int(paciente_id))
        self._render_recetas(recetas)
        log_screen_data_loaded(self._container.connection, "farmacia", len(recetas))
        self.lbl_empty.setVisible(not bool(recetas))
        self.btn_seed_demo.setVisible(not bool(recetas))

    def _load_lineas(self) -> None:
        receta_id = self._selected_id(self.table_recetas)
        if not receta_id:
            return

        lineas = self._container.queries.farmacia.lineas_por_receta(receta_id)
        self._render_lineas(lineas)

    def _on_linea_selected(self) -> None:
        self.btn_dispensar.setEnabled(
            self._can_write and self._selected_id(self.table_lineas) is not None
        )

    def _on_dispensar(self) -> None:
        if not self._can_write:
            return
        linea_id = self._selected_id(self.table_lineas)
        if not linea_id:
            return

        dialog = DispensarDialog(self, container=self._container)
        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()
        if not data:
            return

        receta_id = self._selected_id(self.table_recetas)
        if not receta_id:
            return

        try:
            req = DispensarMedicamentoRequest(
                receta_id=receta_id,
                receta_linea_id=linea_id,
                personal_id=data.personal_id,
                cantidad=data.cantidad,
            )
            DispensarMedicamentoUseCase(self._container).execute(req)
        except PendingWarningsError as w:
            override = OverrideDialog(
                self,
                title="Confirmar dispensación con advertencias",
                warnings=w.warnings,
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
            DispensarMedicamentoUseCase(self._container).execute(req)

        self._load_lineas()

    # ---------------- Render ----------------

    def _render_recetas(self, recetas: list[RecetaRow]) -> None:
        self.table_recetas.setRowCount(0)
        for r in recetas:
            row = self.table_recetas.rowCount()
            self.table_recetas.insertRow(row)
            self.table_recetas.setItem(row, 0, QTableWidgetItem(str(r.id)))
            self.table_recetas.setItem(row, 1, QTableWidgetItem(r.fecha))
            self.table_recetas.setItem(row, 2, QTableWidgetItem(r.medico))
            self.table_recetas.setItem(row, 3, QTableWidgetItem(r.estado))

    def _render_lineas(self, lineas: list[RecetaLineaRow]) -> None:
        self.table_lineas.setRowCount(0)
        for l in lineas:
            row = self.table_lineas.rowCount()
            self.table_lineas.insertRow(row)
            self.table_lineas.setItem(row, 0, QTableWidgetItem(str(l.id)))
            self.table_lineas.setItem(row, 1, QTableWidgetItem(l.medicamento))
            self.table_lineas.setItem(row, 2, QTableWidgetItem(l.dosis))
            self.table_lineas.setItem(row, 3, QTableWidgetItem(str(l.cantidad)))
            self.table_lineas.setItem(row, 4, QTableWidgetItem(str(l.pendiente)))
            self.table_lineas.setItem(row, 5, QTableWidgetItem(l.estado))

    # ---------------- Helpers ----------------

    @staticmethod
    def _selected_id(table: QTableWidget) -> Optional[int]:
        row = table.currentRow()
        if row < 0:
            return None
        try:
            return int(table.item(row, 0).text())
        except Exception:
            return None

    def _select_paciente(self) -> None:
        selection = select_paciente(self, self._container.connection)
        if not selection:
            return
        self._paciente_id = selection.entity_id
        self.input_paciente.setText(selection.display)
        self._load_recetas()

    def _on_seed_demo(self) -> None:
        self._container.demo_ml_facade.seed_demo(SeedDemoDataRequest())
        self._load_recetas()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)
