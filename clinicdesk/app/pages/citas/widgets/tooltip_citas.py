from __future__ import annotations

from clinicdesk.app.application.citas import ATRIBUTOS_CITA, formatear_valor_atributo_cita
from clinicdesk.app.i18n import I18nManager


CLAVES_TOOLTIP_POR_DEFECTO: tuple[str, ...] = (
    "fecha",
    "hora_inicio",
    "hora_fin",
    "paciente",
    "medico",
    "sala",
    "estado",
    "riesgo_ausencia",
    "recordatorio_estado",
    "incidencias",
    "notas_len",
)


def construir_tooltip_cita(i18n: I18nManager, fila: dict[str, object], claves: tuple[str, ...] = CLAVES_TOOLTIP_POR_DEFECTO) -> str:
    etiquetas = {item.clave: item.i18n_key_tooltip for item in ATRIBUTOS_CITA}
    lineas: list[str] = []
    for clave in claves:
        i18n_key = etiquetas.get(clave)
        if not i18n_key:
            continue
        valor = formatear_valor_atributo_cita(clave, fila)
        if not valor:
            continue
        lineas.append(f"{i18n.t(i18n_key)}: {valor}")
    return "\n".join(lineas)
