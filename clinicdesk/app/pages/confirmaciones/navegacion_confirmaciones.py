from __future__ import annotations

import logging

from clinicdesk.app.application.prediccion_ausencias.aviso_salud_prediccion import (
    debe_mostrar_aviso_salud_prediccion,
)
from clinicdesk.app.pages.citas.riesgo_ausencia_dialog import RiesgoAusenciaDialog

LOGGER = logging.getLogger(__name__)


def render_banner(ui, traducir, estado: str) -> None:
    mostrar = debe_mostrar_aviso_salud_prediccion(True, estado)
    ui.banner.setText(traducir("prediccion_ausencias.aviso_salud_prediccion") if mostrar else "")
    ui.banner.setVisible(mostrar)
    ui.btn_ir_prediccion.setVisible(mostrar)


def abrir_riesgo(parent, cita_id: int, on_telemetria) -> None:
    explicacion = parent._container.prediccion_ausencias_facade.obtener_explicacion_riesgo_uc.ejecutar(cita_id)
    salud = parent._container.prediccion_ausencias_facade.obtener_salud_uc.ejecutar()
    RiesgoAusenciaDialog(parent._i18n, explicacion, salud, parent).exec()
    on_telemetria("explicacion_ver_por_que", "ok", cita_id)


def ir_a_prediccion(parent, navegar_prediccion) -> None:
    LOGGER.info(
        "aviso_salud_prediccion_cta",
        extra={"action": "aviso_salud_prediccion_cta", "page": "confirmaciones"},
    )
    navegar_prediccion(parent)
