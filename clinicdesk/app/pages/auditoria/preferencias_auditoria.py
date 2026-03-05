from __future__ import annotations

from clinicdesk.app.application.preferencias.preferencias_usuario import sanitize_search_text


def restaurar_preferencias(*, preferencias_service, ui) -> None:
    if preferencias_service is None:
        return
    filtros = preferencias_service.get().last_search_by_context
    texto = filtros.get("auditoria", "")
    if isinstance(texto, str):
        ui.input_usuario.setText(texto)


def guardar_preferencias(*, preferencias_service, ui) -> None:
    if preferencias_service is None:
        return
    preferencias = preferencias_service.get()
    texto_seguro = sanitize_search_text(ui.input_usuario.text())
    if texto_seguro is None:
        preferencias.last_search_by_context.pop("auditoria", None)
    else:
        preferencias.last_search_by_context["auditoria"] = texto_seguro
    preferencias_service.set(preferencias)
