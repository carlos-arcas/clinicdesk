from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QDialog, QMenu, QMessageBox, QWidget

from clinicdesk.app.application.auditoria_acceso import AccionAuditoriaAcceso, EntidadAuditoriaAcceso
from clinicdesk.app.application.historial_paciente import (
    BuscarHistorialCitasPaciente,
    BuscarHistorialRecetasPaciente,
    ObtenerResumenHistorialPaciente,
)
from clinicdesk.app.application.usecases.obtener_detalle_cita import ObtenerDetalleCita
from clinicdesk.app.application.usecases.obtener_historial_paciente import ObtenerHistorialPaciente
from clinicdesk.app.application.usecases.pacientes_crud import (
    CrearPacienteUseCase,
    DesactivarPacienteUseCase,
    EditarPacienteUseCase,
)
from clinicdesk.app.application.usecases.registrar_auditoria_acceso import RegistrarAuditoriaAcceso
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pacientes.dialogs.historial_paciente_dialog import HistorialPacienteDialog
from clinicdesk.app.pages.pacientes.dialogs.paciente_form import PacienteFormDialog
from clinicdesk.app.pages.shared.crud_page_helpers import confirm_deactivation
from clinicdesk.app.ui.error_presenter import present_error


def on_nuevo(*, parent: QWidget, uc_crear: CrearPacienteUseCase, on_success: Callable[[], None]) -> None:
    dialog = PacienteFormDialog(parent)
    if dialog.exec() != QDialog.Accepted:
        return
    data = dialog.get_data()
    if not data:
        return
    try:
        uc_crear.execute(data.paciente)
    except Exception as exc:
        _presentar_error(
            parent=parent, exc=exc, tipo_doc=data.paciente.tipo_documento.value, documento=data.paciente.documento
        )
        return
    on_success()


def on_editar(
    *,
    parent: QWidget,
    selected_id: int | None,
    obtener_paciente: Callable[[int], object | None],
    uc_editar: EditarPacienteUseCase,
    on_success: Callable[[], None],
) -> None:
    if not selected_id:
        return
    paciente = obtener_paciente(selected_id)
    if not paciente:
        return
    dialog = PacienteFormDialog(parent)
    dialog.set_paciente(paciente)
    if dialog.exec() != QDialog.Accepted:
        return
    data = dialog.get_data()
    if not data:
        return
    try:
        uc_editar.execute(data.paciente)
    except Exception as exc:
        _presentar_error(
            parent=parent, exc=exc, tipo_doc=data.paciente.tipo_documento.value, documento=data.paciente.documento
        )
        return
    on_success()


def on_desactivar(
    *,
    parent: QWidget,
    selected_id: int | None,
    uc_desactivar: DesactivarPacienteUseCase,
    on_success: Callable[[], None],
) -> None:
    if not selected_id:
        return
    if not confirm_deactivation(parent, module_title="Pacientes", entity_label="paciente"):
        return
    uc_desactivar.execute(selected_id)
    on_success()


def on_historial(
    *,
    parent: QWidget,
    i18n: I18nManager,
    selected_id: int | None,
    registrar_auditoria: RegistrarAuditoriaAcceso,
    contexto_usuario: object,
    buscar_citas_uc: BuscarHistorialCitasPaciente,
    buscar_recetas_uc: BuscarHistorialRecetasPaciente,
    resumen_uc: ObtenerResumenHistorialPaciente,
    historial_legacy_uc: ObtenerHistorialPaciente,
    detalle_cita_uc: ObtenerDetalleCita,
) -> None:
    if not selected_id:
        return
    registrar_auditoria.execute(
        contexto_usuario=contexto_usuario,
        accion=AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE,
        entidad_tipo=EntidadAuditoriaAcceso.PACIENTE,
        entidad_id=selected_id,
    )
    HistorialPacienteDialog(
        i18n,
        paciente_id=selected_id,
        buscar_citas_uc=buscar_citas_uc,
        buscar_recetas_uc=buscar_recetas_uc,
        resumen_uc=resumen_uc,
        historial_legacy_uc=historial_legacy_uc,
        detalle_cita_uc=detalle_cita_uc,
        auditoria_uc=registrar_auditoria,
        contexto_usuario=contexto_usuario,
        parent=parent,
    ).exec()


def open_context_menu(
    *,
    parent: QWidget,
    table,
    pos: QPoint,
    i18n: I18nManager,
    can_write: bool,
    has_selection: bool,
    on_nuevo_cb: Callable[[], None],
    on_editar_cb: Callable[[], None],
    on_desactivar_cb: Callable[[], None],
    on_historial_cb: Callable[[], None],
) -> None:
    row = table.rowAt(pos.y())
    if row >= 0:
        table.setCurrentCell(row, 0)
    menu = QMenu(parent)
    action_new = menu.addAction("Nuevo")
    action_edit = menu.addAction("Editar")
    action_delete = menu.addAction("Desactivar")
    action_historial = menu.addAction(i18n.t("pacientes.historial.boton"))
    action_edit.setEnabled(has_selection)
    action_delete.setEnabled(has_selection)
    action_historial.setEnabled(has_selection)
    if not can_write:
        action_new.setEnabled(False)
        action_edit.setEnabled(False)
        action_delete.setEnabled(False)
    action = menu.exec(table.viewport().mapToGlobal(pos))
    if action == action_new:
        on_nuevo_cb()
    elif action == action_edit:
        on_editar_cb()
    elif action == action_delete:
        on_desactivar_cb()
    elif action == action_historial:
        on_historial_cb()


def open_csv_dialog(parent: QWidget) -> None:
    open_dialog = getattr(parent.window(), "open_csv_dialog", None)
    if callable(open_dialog):
        open_dialog()
        return
    QMessageBox.information(
        parent,
        "CSV",
        "Esta acción está disponible en la ventana principal. Ejecuta la aplicación con: python -m clinicdesk",
    )


def _presentar_error(*, parent: QWidget, exc: Exception, tipo_doc: str, documento: str) -> None:
    context = f"Tipo documento: {tipo_doc}\nDocumento: {documento}"
    present_error(parent, exc, context=context)
