from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtCore import QThread, Qt
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
from clinicdesk.app.application.usecases.obtener_detalle_cita import ObtenerDetalleCita
from clinicdesk.app.application.auditoria_acceso import AccionAuditoriaAcceso, EntidadAuditoriaAcceso
from clinicdesk.app.application.historial_paciente import (
    BuscarHistorialCitasPaciente,
    BuscarHistorialRecetasPaciente,
    ObtenerResumenHistorialPaciente,
)
from clinicdesk.app.application.usecases.obtener_historial_paciente import ObtenerHistorialPaciente
from clinicdesk.app.application.usecases.registrar_auditoria_acceso import RegistrarAuditoriaAcceso
from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.pages.pacientes.dialogs.historial_paciente_dialog import HistorialPacienteDialog
from clinicdesk.app.pages.pacientes.dialogs.paciente_form import PacienteFormDialog
from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget
from clinicdesk.app.pages.shared.crud_page_helpers import confirm_deactivation, set_buttons_enabled
from clinicdesk.app.pages.shared.table_utils import apply_row_style, set_item
from clinicdesk.app.queries.historial_paciente_queries import HistorialPacienteQueries
from clinicdesk.app.queries.historial_listados_queries import HistorialListadosQueries
from clinicdesk.app.queries.pacientes_queries import PacienteRow
from clinicdesk.app.queries.recetas_queries import RecetasQueries
from clinicdesk.app.ui.error_presenter import present_error
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget
from clinicdesk.app.infrastructure.sqlite.db_path import resolver_db_path_desde_conexion
from clinicdesk.app.ui.workers.listado_async_workers import CargaPacientesWorker


LOGGER = logging.getLogger(__name__)


class PagePacientes(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._db_path = resolver_db_path_desde_conexion(container.connection)
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

        self._uc_detalle_cita = ObtenerDetalleCita(HistorialPacienteQueries(container.connection))
        historial_queries = HistorialListadosQueries(container.connection)
        self._uc_buscar_historial_citas = BuscarHistorialCitasPaciente(historial_queries)
        self._uc_buscar_historial_recetas = BuscarHistorialRecetasPaciente(historial_queries)
        self._uc_resumen_historial = ObtenerResumenHistorialPaciente(historial_queries)
        self._uc_auditoria_acceso = RegistrarAuditoriaAcceso(container.auditoria_accesos_repo)
        self._thread_carga: QThread | None = None
        self._worker_carga: CargaPacientesWorker | None = None
        self._token_carga = 0

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

        self._estado_pantalla = EstadoPantallaWidget(self._i18n, self)
        contenido = QWidget(self)
        contenido_layout = QVBoxLayout(contenido)
        contenido_layout.setContentsMargins(0, 0, 0, 0)
        contenido_layout.addWidget(self.table)
        self._estado_pantalla.set_content(contenido)

        root.addWidget(self.filtros)
        root.addLayout(actions)
        root.addWidget(self._estado_pantalla)

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

    def _set_busy(self, activo: bool, mensaje_key: str) -> None:
        window = self.window()
        set_busy = getattr(window, "set_busy", None)
        if callable(set_busy):
            set_busy(activo, mensaje_key)

    def _toast_success(self, key: str) -> None:
        toast = getattr(self.window(), "toast_success", None)
        if callable(toast):
            toast(key)

    def _toast_error(self, key: str) -> None:
        toast = getattr(self.window(), "toast_error", None)
        if callable(toast):
            toast(key)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self._token_carga += 1
        token = self._token_carga
        selected_id = self._selected_id()
        activo = self.filtros.activo()
        texto = normalize_search_text(self.filtros.texto())
        self._estado_pantalla.set_loading("ux_states.pacientes.loading")
        self._set_busy(True, "busy.loading_pacientes")
        self._arrancar_worker_carga(token=token, selected_id=selected_id, activo=activo, texto=texto)

    def _arrancar_worker_carga(self, *, token: int, selected_id: int | None, activo: bool, texto: str) -> None:
        if self._thread_carga is not None and self._thread_carga.isRunning():
            return
        self._thread_carga = QThread(self)
        self._worker_carga = CargaPacientesWorker(self._db_path, activo, texto)
        self._worker_carga.moveToThread(self._thread_carga)
        self._thread_carga.started.connect(self._worker_carga.run)
        self._worker_carga.finished_ok.connect(lambda payload: self._on_carga_ok(payload, token, selected_id))
        self._worker_carga.finished_error.connect(lambda error: self._on_carga_error(error, token))
        self._worker_carga.finished.connect(self._thread_carga.quit)
        self._worker_carga.finished.connect(self._worker_carga.deleteLater)
        self._thread_carga.finished.connect(self._thread_carga.deleteLater)
        self._thread_carga.finished.connect(self._reset_carga_worker)
        self._thread_carga.start()

    def _reset_carga_worker(self) -> None:
        self._thread_carga = None
        self._worker_carga = None

    def _on_carga_ok(self, payload: object, token: int, selected_id: int | None) -> None:
        if token != self._token_carga or not isinstance(payload, dict):
            return
        self._set_busy(False, "busy.loading_pacientes")
        rows = payload.get("rows", [])
        total_base = int(payload.get("total_base", len(rows)))
        self.filtros.set_contador(len(rows), total_base)
        self._render(rows)
        if selected_id is not None:
            self._select_by_id(selected_id)
        self._update_buttons()
        if not rows:
            self._estado_pantalla.set_empty(
                "ux_states.pacientes.empty",
                cta_text_key="ux_states.pacientes.cta_refresh",
                on_cta=self._refresh,
            )
            self._toast_success("toast.refresh_ok_pacientes")
            return
        self._estado_pantalla.set_content(self.table.parentWidget())
        self._toast_success("toast.refresh_ok_pacientes")

    def _on_carga_error(self, error_type: str, token: int) -> None:
        if token != self._token_carga:
            return
        self._set_busy(False, "busy.loading_pacientes")
        LOGGER.warning(
            "pacientes_carga_error",
            extra={"action": "pacientes_carga_error", "error": error_type},
        )
        self._estado_pantalla.set_error(
            "ux_states.pacientes.error",
            detalle_tecnico=error_type,
            on_retry=self._refresh,
        )
        self._toast_error("toast.refresh_fail")

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
            context = f"Tipo documento: {data.paciente.tipo_documento.value}\nDocumento: {data.paciente.documento}"
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
            context = f"Tipo documento: {data.paciente.tipo_documento.value}\nDocumento: {data.paciente.documento}"
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
            "Esta acción está disponible en la ventana principal. Ejecuta la aplicación con: python -m clinicdesk",
        )

    def _reset_filters(self) -> None:
        self.filtros.limpiar()

    def _on_historial(self) -> None:
        paciente_id = self._selected_id()
        if not paciente_id:
            return
        self._uc_auditoria_acceso.execute(
            contexto_usuario=self._container.user_context,
            accion=AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE,
            entidad_tipo=EntidadAuditoriaAcceso.PACIENTE,
            entidad_id=paciente_id,
        )
        dialog = HistorialPacienteDialog(
            self._i18n,
            paciente_id=paciente_id,
            buscar_citas_uc=self._uc_buscar_historial_citas,
            buscar_recetas_uc=self._uc_buscar_historial_recetas,
            resumen_uc=self._uc_resumen_historial,
            historial_legacy_uc=self._uc_historial,
            detalle_cita_uc=self._uc_detalle_cita,
            auditoria_uc=self._uc_auditoria_acceso,
            contexto_usuario=self._container.user_context,
            parent=self,
        )
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
    logging.getLogger(__name__).info("Este módulo no se ejecuta directamente. Usa: python -m clinicdesk")
    raise SystemExit(2)
