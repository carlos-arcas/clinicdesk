from __future__ import annotations

import logging

from clinicdesk.app.application.citas.filtros import redactar_texto_busqueda

LOGGER = logging.getLogger(__name__)


def log_carga(page, reset: bool) -> None:
    LOGGER.info(
        "confirmaciones_carga",
        extra={
            "action": "confirmaciones_carga",
            "reset": reset,
            "offset": page._offset,
            "texto_redactado": redactar_texto_busqueda(page._ui.txt_buscar.text()),
            "riesgo_filtro": str(page._ui.cmb_riesgo.currentData()),
            "recordatorio_filtro": str(page._ui.cmb_recordatorio.currentData()),
        },
    )


def registrar_telemetria(page, evento: str, resultado: str, cita_id: int | None) -> None:
    try:
        page._uc_telemetria.ejecutar(
            contexto_usuario=page._container.user_context,
            evento=evento,
            contexto=f"page=confirmaciones;resultado={resultado}",
            entidad_tipo="cita",
            entidad_id=cita_id,
        )
    except Exception:
        return
