from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem, QWidget

from clinicdesk.app.pages.confirmaciones.acciones_whatsapp_rapido import estado_accion_whatsapp_rapida
from clinicdesk.app.pages.confirmaciones.contratos_ui import ConfirmacionesUIRefs
from clinicdesk.app.pages.confirmaciones.tabla_actions import crear_actions_confirmacion
from clinicdesk.app.ui.ux.estados_listado import ConfigEstadoListado, aplicar_estado_listado
from clinicdesk.app.ui.viewmodels.contratos import EstadoListado

_COL_CHECK = 0


def render_estado(
    ui: ConfirmacionesUIRefs,
    estado: EstadoListado[object],
    *,
    on_retry: Callable[[], None],
    render_rows: Callable[[list[object]], None],
) -> None:
    aplicar_estado_listado(
        estado_widget=ui.estado_pantalla,
        estado=estado,
        contenido=ui.contenido_tabla,
        config=ConfigEstadoListado(
            loading_key="ux_states.confirmaciones.loading",
            empty_key="ux_states.confirmaciones.empty",
            empty_cta_key="ux_states.confirmaciones.cta_refresh",
            error_key="ux_states.confirmaciones.error",
        ),
        on_retry=on_retry,
        render_rows=render_rows,
    )


def render_tabla(
    *,
    ui: ConfirmacionesUIRefs,
    rows: list[object],
    seleccionadas: set[int],
    cita_en_preparacion: int | None,
    traducir: Callable[[str], str],
    on_abrir_riesgo: Callable[[int], None],
    on_preparar_whatsapp: Callable[[object], None],
) -> None:
    ui.table.blockSignals(True)
    ui.table.setRowCount(len(rows))
    for row, item in enumerate(rows):
        _render_row(
            ui=ui,
            row=row,
            item=item,
            seleccionadas=seleccionadas,
            cita_en_preparacion=cita_en_preparacion,
            traducir=traducir,
            on_abrir_riesgo=on_abrir_riesgo,
            on_preparar_whatsapp=on_preparar_whatsapp,
        )
    ui.table.blockSignals(False)


def apply_selection(ui: ConfirmacionesUIRefs, cita_id: int) -> bool:
    for row in range(ui.table.rowCount()):
        item = ui.table.item(row, _COL_CHECK)
        if item is not None and item.data(Qt.UserRole) == cita_id:
            ui.table.setCurrentCell(row, _COL_CHECK)
            return True
    return False


def _render_row(
    *,
    ui: ConfirmacionesUIRefs,
    row: int,
    item,
    seleccionadas: set[int],
    cita_en_preparacion: int | None,
    traducir: Callable[[str], str],
    on_abrir_riesgo: Callable[[int], None],
    on_preparar_whatsapp: Callable[[object], None],
) -> None:
    selector = QTableWidgetItem()
    selector.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
    selector.setCheckState(Qt.Checked if item.cita_id in seleccionadas else Qt.Unchecked)
    selector.setData(Qt.UserRole, item.cita_id)
    ui.table.setItem(row, 0, selector)
    inicio = item.inicio
    ui.table.setItem(row, 1, QTableWidgetItem(inicio[:10]))
    ui.table.setItem(row, 2, QTableWidgetItem(inicio[11:16]))
    ui.table.setItem(row, 3, QTableWidgetItem(item.paciente))
    ui.table.setItem(row, 4, QTableWidgetItem(item.medico))
    ui.table.setItem(row, 5, QTableWidgetItem(item.estado_cita))
    ui.table.setItem(row, 6, QTableWidgetItem(traducir(f"confirmaciones.riesgo.{item.riesgo.lower()}")))
    ui.table.setItem(
        row,
        7,
        QTableWidgetItem(traducir(f"confirmaciones.recordatorio.{item.recordatorio_estado.lower()}")),
    )
    ui.table.setCellWidget(
        row,
        8,
        _crear_actions(
            ui.table,
            item,
            traducir=traducir,
            cita_en_preparacion=cita_en_preparacion,
            on_abrir_riesgo=on_abrir_riesgo,
            on_preparar_whatsapp=on_preparar_whatsapp,
        ),
    )


def _crear_actions(
    table: QWidget,
    item,
    *,
    traducir: Callable[[str], str],
    cita_en_preparacion: int | None,
    on_abrir_riesgo: Callable[[int], None],
    on_preparar_whatsapp: Callable[[object], None],
) -> QWidget:
    estado = estado_accion_whatsapp_rapida(item.riesgo, item.recordatorio_estado, item.tiene_telefono)
    tooltip = traducir(estado.tooltip_key) if estado.tooltip_key else ""
    return crear_actions_confirmacion(
        table,
        traducir("confirmaciones.accion.ver_riesgo"),
        traducir("confirmaciones.accion.preparar_whatsapp_rapido"),
        traducir("confirmaciones.accion.preparando_fila"),
        estado,
        cita_en_preparacion == item.cita_id,
        tooltip,
        lambda: on_abrir_riesgo(item.cita_id),
        lambda: on_preparar_whatsapp(item),
    )
