from __future__ import annotations

from clinicdesk.app.pages.auditoria.contratos_ui import AuditoriaUIRefs
from clinicdesk.app.pages.shared.table_utils import set_item


def render_tabla(ui: AuditoriaUIRefs, items: list[object], *, traducir) -> None:
    ui.tabla.setRowCount(0)
    for row, item in enumerate(items):
        ui.tabla.insertRow(row)
        set_item(ui.tabla, row, 0, item.timestamp_utc)
        set_item(ui.tabla, row, 1, item.usuario)
        set_item(ui.tabla, row, 2, traducir("comun.si") if item.modo_demo else traducir("comun.no"))
        set_item(ui.tabla, row, 3, item.accion)
        set_item(ui.tabla, row, 4, item.entidad_tipo)
        set_item(ui.tabla, row, 5, item.entidad_id)


def render_estado(ui: AuditoriaUIRefs, *, estado: str, mostrados: int, total: int, traducir) -> None:
    textos = {
        "loading": traducir("auditoria.estado.cargando"),
        "loading_more": traducir("auditoria.estado.cargando_mas"),
        "empty": traducir("auditoria.estado.vacio"),
        "error": traducir("auditoria.estado.error"),
        "error_more": traducir("auditoria.estado.error_cargar_mas"),
        "ok": traducir("auditoria.estado.mostrando_x_de_y").format(mostrados=mostrados, total=total),
        "idle": "",
    }
    ui.lbl_estado.setText(textos[estado])
    ui.btn_reintentar.setVisible(estado in {"error", "error_more"})
    ui.btn_exportar.setEnabled(total > 0)
    ui.btn_cargar_mas.setVisible(mostrados < total)
    ui.btn_cargar_mas.setEnabled(estado == "ok" and mostrados < total)


def render_resumen(ui: AuditoriaUIRefs, resumen, traducir) -> None:
    ui.lbl_accesos_hoy.setText(str(resumen.accesos_hoy))
    ui.lbl_accesos_7_dias.setText(str(resumen.accesos_ultimos_7_dias))
    top = [f"{item.accion} ({item.total})" for item in resumen.top_acciones]
    ui.lbl_top_acciones.setText(", ".join(top) if top else traducir("auditoria.resumen.sin_datos"))


def apply_selection(ui: AuditoriaUIRefs, item_id: int | None) -> None:
    if item_id is None:
        ui.tabla.clearSelection()
        return
    for row in range(ui.tabla.rowCount()):
        item = ui.tabla.item(row, 5)
        if item is not None and item.text() == str(item_id):
            ui.tabla.setCurrentCell(row, 0)
            return
