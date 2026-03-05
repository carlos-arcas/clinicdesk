from __future__ import annotations

from clinicdesk.app.application.preferencias.preferencias_usuario import sanitize_search_text
from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget


def restaurar_preferencias(*, preferencias_service, filtros_widget: FiltroListadoWidget) -> None:
    preferencias = preferencias_service.get()
    filtros = preferencias.filtros_pacientes
    texto = filtros.get("texto", "")
    filtros_widget.txt_busqueda.setText(texto if isinstance(texto, str) else "")
    activo = filtros.get("activo")
    if activo is True:
        index = filtros_widget.cbo_estado.findText("Activos")
    elif activo is False:
        index = filtros_widget.cbo_estado.findText("Inactivos")
    else:
        index = filtros_widget.cbo_estado.findText("Todos")
    filtros_widget.cbo_estado.setCurrentIndex(index if index >= 0 else 0)


def guardar_preferencias(*, preferencias_service, filtros_widget: FiltroListadoWidget) -> None:
    preferencias = preferencias_service.get()
    texto_seguro = sanitize_search_text(filtros_widget.texto())
    preferencias.filtros_pacientes = {
        "activo": filtros_widget.activo(),
        "texto": texto_seguro or "",
    }
    if texto_seguro is None:
        preferencias.last_search_by_context.pop("pacientes", None)
    else:
        preferencias.last_search_by_context["pacientes"] = texto_seguro
    preferencias_service.set(preferencias)
