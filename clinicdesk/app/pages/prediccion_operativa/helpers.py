from __future__ import annotations

from clinicdesk.app.application.prediccion_operativa.dtos import ExplicacionOperativaDTO
from clinicdesk.app.i18n import I18nManager


ESTADO_SALUD_CLAVE_I18N: dict[str, str] = {
    "VERDE": "prediccion_operativa.estado.bien",
    "AMARILLO": "prediccion_operativa.estado.atencion",
    "ROJO": "prediccion_operativa.estado.necesita_revision",
}


def resolver_clave_estado_salud(estado: str) -> str:
    return ESTADO_SALUD_CLAVE_I18N.get(estado, "prediccion_operativa.estado.no_disponible")


def resolver_texto_estimacion(nivel: str, i18n: I18nManager) -> str:
    key = nivel.lower() if nivel else "no_disponible"
    return i18n.t(f"citas.prediccion_operativa.valor.{key}")


def construir_bullets_explicacion(dto: ExplicacionOperativaDTO, i18n: I18nManager) -> str:
    items = [i18n.t(key) for key in dto.motivos_i18n_keys[:3]]
    if not items:
        items = [i18n.t("citas.prediccion_operativa.motivo.no_disponible")]
    return "\n".join(f"• {item}" for item in items)


def debe_cargar_previsualizacion(mostrar_en_agenda: bool) -> bool:
    return mostrar_en_agenda
