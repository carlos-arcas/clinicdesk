from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
    QDialog,
    QMenu,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.application.usecases.pacientes_crud import (
    CrearPacienteUseCase,
    DesactivarPacienteUseCase,
    EditarPacienteUseCase,
)
from clinicdesk.app.application.services.pacientes_listado_contrato import ContratoListadoPacientesService
from clinicdesk.app.application.usecases.obtener_historial_paciente import ObtenerHistorialPaciente
from clinicdesk.app.common.search_utils import has_search_values, normalize_search_text
from clinicdesk.app.pages.pacientes.dialogs.historial_paciente_dialog import HistorialPacienteDialog
from clinicdesk.app.pages.pacientes.dialogs.paciente_form import PacienteFormDialog
from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget
from clinicdesk.app.pages.shared.crud_page_helpers import confirm_deactivation, set_buttons_enabled
from clinicdesk.app.pages.shared.table_utils import apply_row_style, set_item
from clinicdesk.app.queries.historial_paciente_queries import HistorialPacienteQueries
from clinicdesk.app.queries.pacientes_queries import PacientesQueries, PacienteRow
from clinicdesk.app.queries.recetas_queries import RecetasQueries
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
        self._i18n = I18nManager("es")
        self._contrato_listado = ContratoListadoPacientesService()
        self._columnas = self._contrato_listado.atributos_disponibles()
        self._uc_historial = ObtenerHistorialPaciente(
            pacientes_gateway=container.pacientes_repo,
            citas_gateway=HistorialPacienteQueries(container.connection),
            recetas_gateway=RecetasQueries(container.connection),
        )

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
        self.btn_historial = QPushButton(self._i18n.t("pacientes.historial.boton"))
        self.btn_csv = QPushButton("Importar/Exportar CSV…")
        self.btn_editar.setEnabled(False)
        self.btn_desactivar.setEnabled(False)
        self.btn_historial.setEnabled(False)
        self.btn_nuevo.setEnabled(self._can_write)
        actions.addWidget(self.btn_nuevo)
        actions.addWidget(self.btn_editar)
        actions.addWidget(self.btn_desactivar)
        actions.addWidget(self.btn_historial)
        actions.addWidget(self.btn_csv)
        actions.addStretch(1)

        self.table = QTableWidget(0, len(self._columnas))
        self.table.setHorizontalHeaderLabels([self._i18n.t(col.clave_i18n) for col in self._columnas])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        root.addWidget(self.filtros)
        root.addLayout(actions)
        root.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.filtros.filtros_cambiados.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.itemDoubleClicked.connect(lambda _: self._on_historial())
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_editar.clicked.connect(self._on_editar)
        self.btn_desactivar.clicked.connect(self._on_desactivar)
        self.btn_historial.clicked.connect(self._on_historial)
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
            for col_idx, descriptor in enumerate(self._columnas):
                valor = self._valor_columna(p, descriptor.nombre)
                valor_listado = self._contrato_listado.formatear_valor_listado(descriptor.nombre, valor)
                set_item(self.table, row, col_idx, valor_listado)
            tooltip = self._tooltip_mascarado(p)
            apply_row_style(self.table, row, inactive=not p.activo, tooltip=tooltip)

    def _valor_columna(self, paciente: PacienteRow, nombre_columna: str) -> object:
        if nombre_columna == "activo":
            return self._i18n.t("comun.si") if paciente.activo else self._i18n.t("comun.no")
        return getattr(paciente, nombre_columna, "")

    def _tooltip_mascarado(self, paciente: PacienteRow) -> str:
        documento = self._contrato_listado.formatear_valor_listado("documento", paciente.documento)
        telefono = self._contrato_listado.formatear_valor_listado("telefono", paciente.telefono)
        estado = self._i18n.t("comun.si") if paciente.activo else self._i18n.t("comun.no")
        return self._i18n.t("pacientes.tooltip.listado").format(documento=documento, telefono=telefono, estado=estado)

    def _update_buttons(self) -> None:
        if not self._can_write:
            self.btn_editar.setEnabled(False)
            self.btn_desactivar.setEnabled(False)
            self.btn_historial.setEnabled(self._selected_id() is not None)
            return
        set_buttons_enabled(
            has_selection=self._selected_id() is not None,
            buttons=[self.btn_editar, self.btn_desactivar],
        )
        self.btn_historial.setEnabled(self._selected_id() is not None)

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
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        item = self.table.item(current_row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
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

    def _on_historial(self) -> None:
        paciente_id = self._selected_id()
        if not paciente_id:
            return
        dialog = HistorialPacienteDialog(self._i18n, self)
        dialog.setWindowTitle(self._i18n.t("pacientes.historial.titulo"))
        dialog.render_cargando()
        resultado = self._uc_historial.execute(paciente_id)
        if resultado is None:
            dialog.render_error()
        else:
            dialog.render_historial(resultado)
        dialog.exec()

    def _open_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        menu = QMenu(self)
        action_new = menu.addAction("Nuevo")
        action_edit = menu.addAction("Editar")
        action_delete = menu.addAction("Desactivar")
        action_historial = menu.addAction(self._i18n.t("pacientes.historial.boton"))
        has_selection = self._selected_id() is not None
        action_edit.setEnabled(has_selection)
        action_delete.setEnabled(has_selection)
        action_historial.setEnabled(has_selection)
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
        elif action == action_historial:
            self._on_historial()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)
