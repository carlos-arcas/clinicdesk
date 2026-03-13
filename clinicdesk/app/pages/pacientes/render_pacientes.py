from __future__ import annotations

from typing import Callable

from clinicdesk.app.pages.pacientes.contratos_ui import PacientesUIRefs
from clinicdesk.app.pages.shared.table_utils import apply_row_style, set_item
from clinicdesk.app.queries.pacientes_queries import PacienteRow
from clinicdesk.app.ui.ux.estados_listado import ConfigEstadoListado, aplicar_estado_listado
from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla


def render_estado(
    ui: PacientesUIRefs,
    estado: EstadoListado[PacienteRow],
    *,
    on_retry: Callable[[], None],
    render_rows: Callable[[list[PacienteRow]], None],
    apply_selected_id: Callable[[int], None],
    update_buttons: Callable[[], None],
) -> None:
    aplicar_estado_listado(
        estado_widget=ui.estado_pantalla,
        estado=estado,
        contenido=ui.contenido_tabla,
        config=ConfigEstadoListado(
            loading_key="ux_states.pacientes.loading",
            empty_key="ux_states.pacientes.empty",
            empty_cta_key="ux_states.pacientes.cta_refresh",
            error_key="ux_states.pacientes.error",
        ),
        on_retry=on_retry,
        render_rows=render_rows,
    )
    if estado.estado_pantalla is EstadoPantalla.CONTENT and estado.seleccion_id is not None:
        apply_selected_id(estado.seleccion_id)
    update_buttons()


def render_tabla(
    ui: PacientesUIRefs,
    rows: list[PacienteRow],
    *,
    columnas: list[object],
    obtener_valor_columna: Callable[[PacienteRow, str], object],
    obtener_tooltip: Callable[[PacienteRow], str],
    formatear_valor_listado: Callable[[str, object], str],
) -> None:
    ui.table.setRowCount(0)
    for paciente in rows:
        row = ui.table.rowCount()
        ui.table.insertRow(row)
        for col_idx, descriptor in enumerate(columnas):
            valor = obtener_valor_columna(paciente, descriptor.nombre)
            valor_listado = formatear_valor_listado(descriptor.nombre, valor)
            set_item(ui.table, row, col_idx, valor_listado)
        apply_row_style(ui.table, row, inactive=not paciente.activo, tooltip=obtener_tooltip(paciente))


def apply_selection(ui: PacientesUIRefs, paciente_id: int) -> None:
    for row in range(ui.table.rowCount()):
        item = ui.table.item(row, 0)
        if item and item.text() == str(paciente_id):
            ui.table.setCurrentCell(row, 0)
            return


def selected_id(ui: PacientesUIRefs) -> int | None:
    current_row = ui.table.currentRow()
    if current_row < 0:
        return None
    item = ui.table.item(current_row, 0)
    if item is None:
        return None
    try:
        return int(item.text())
    except ValueError:
        return None


def update_action_buttons(ui: PacientesUIRefs, *, can_write: bool, set_buttons_enabled) -> None:
    has_selection = selected_id(ui) is not None
    if not can_write:
        ui.btn_editar.setEnabled(False)
        ui.btn_desactivar.setEnabled(False)
        ui.btn_historial.setEnabled(has_selection)
        return
    set_buttons_enabled(has_selection=has_selection, buttons=[ui.btn_editar, ui.btn_desactivar])
    ui.btn_historial.setEnabled(has_selection)
