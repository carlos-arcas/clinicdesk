from __future__ import annotations

from clinicdesk.app.application.preferencias.preferencias_usuario import sanitize_search_text


def restaurar_preferencias(*, preferencias_service, ui) -> None:
    preferencias = preferencias_service.get()
    filtros = preferencias.filtros_confirmaciones
    _set_current_data(ui.cmb_rango, str(filtros.get("rango", "7D")))
    _set_current_data(ui.cmb_riesgo, str(filtros.get("riesgo", "TODOS")))
    _set_current_data(ui.cmb_recordatorio, str(filtros.get("recordatorio", "TODOS")))
    ui.txt_buscar.setText(str(filtros.get("texto", "")))


def guardar_preferencias(*, preferencias_service, ui) -> None:
    preferencias = preferencias_service.get()
    texto_seguro = sanitize_search_text(ui.txt_buscar.text())
    preferencias.filtros_confirmaciones = {
        "rango": str(ui.cmb_rango.currentData()),
        "riesgo": str(ui.cmb_riesgo.currentData()),
        "recordatorio": str(ui.cmb_recordatorio.currentData()),
        "texto": texto_seguro or "",
    }
    if texto_seguro is None:
        preferencias.last_search_by_context.pop("confirmaciones", None)
    else:
        preferencias.last_search_by_context["confirmaciones"] = texto_seguro
    preferencias_service.set(preferencias)


def _set_current_data(combo, value: str) -> None:
    idx = combo.findData(value)
    if idx >= 0:
        combo.setCurrentIndex(idx)
