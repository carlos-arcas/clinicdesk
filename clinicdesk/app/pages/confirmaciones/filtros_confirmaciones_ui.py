from __future__ import annotations

from datetime import date, timedelta

from clinicdesk.app.pages.confirmaciones.columnas import claves_columnas_confirmaciones


def labels_columnas_confirmaciones(traducir) -> list[str]:
    mapa = {
        "seleccion": traducir("confirmaciones.seleccion.seleccionar"),
        "fecha": traducir("confirmaciones.col.fecha"),
        "hora": traducir("confirmaciones.col.hora"),
        "paciente": traducir("confirmaciones.col.paciente"),
        "medico": traducir("confirmaciones.col.medico"),
        "estado": traducir("confirmaciones.col.estado"),
        "riesgo": traducir("confirmaciones.col.riesgo"),
        "recordatorio": traducir("confirmaciones.col.recordatorio"),
        "acciones": traducir("confirmaciones.col.acciones"),
    }
    return [mapa[clave] for clave in claves_columnas_confirmaciones()]


def set_filter_options(ui, traducir, on_rango_changed) -> None:
    ui.cmb_rango.clear()
    ui.cmb_rango.addItem(traducir("confirmaciones.filtro.rango.hoy"), "HOY")
    ui.cmb_rango.addItem(traducir("confirmaciones.filtro.rango.7d"), "7D")
    ui.cmb_rango.addItem(traducir("confirmaciones.filtro.rango.30d"), "30D")
    ui.cmb_rango.addItem(traducir("confirmaciones.filtro.rango.custom"), "CUSTOM")
    ui.cmb_riesgo.clear()
    ui.cmb_riesgo.addItem(traducir("confirmaciones.filtro.riesgo.todos"), "TODOS")
    ui.cmb_riesgo.addItem(traducir("confirmaciones.filtro.riesgo.alto_medio"), "ALTO_MEDIO")
    ui.cmb_riesgo.addItem(traducir("confirmaciones.filtro.riesgo.solo_alto"), "SOLO_ALTO")
    ui.cmb_recordatorio.clear()
    ui.cmb_recordatorio.addItem(traducir("confirmaciones.filtro.recordatorio.todos"), "TODOS")
    ui.cmb_recordatorio.addItem(traducir("confirmaciones.filtro.recordatorio.sin_preparar"), "SIN_PREPARAR")
    ui.cmb_recordatorio.addItem(traducir("confirmaciones.filtro.recordatorio.no_enviado"), "NO_ENVIADO")
    on_rango_changed()


def on_rango_changed(ui) -> None:
    mode = ui.cmb_rango.currentData()
    today = date.today()
    end = today if mode == "HOY" else today + timedelta(days=30 if mode == "30D" else 7)
    if mode != "CUSTOM":
        ui.desde.setDate(today)
        ui.hasta.setDate(end)
    ui.desde.setEnabled(mode == "CUSTOM")
    ui.hasta.setEnabled(mode == "CUSTOM")
