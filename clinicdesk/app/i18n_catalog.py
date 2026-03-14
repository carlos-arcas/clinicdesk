from __future__ import annotations

from clinicdesk.app.i18n_catalogos.core import I18N_CATALOGO_CORE
from clinicdesk.app.i18n_catalogos.pred import I18N_CATALOGO_PREDICCION
from clinicdesk.app.i18n_catalogos.ux import I18N_CATALOGO_UX
from clinicdesk.app.i18n_ml_operativa_catalog import ML_OPERATIVA_TRANSLATIONS
from clinicdesk.app.i18n_prediccion_recordatorio_catalog import PREDICCION_RECORDATORIO_TRANSLATIONS
from clinicdesk.app.i18n_prediccion_resultados_catalog import PREDICCION_RESULTADOS_TRANSLATIONS
from clinicdesk.app.i18n_recordatorio_catalog import RECORDATORIO_TRANSLATIONS


def _merge_catalogos_sin_duplicados(*catalogos: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    catalogo_final: dict[str, dict[str, str]] = {}
    for catalogo in catalogos:
        for idioma, entradas in catalogo.items():
            destino = catalogo_final.setdefault(idioma, {})
            for clave, valor in entradas.items():
                if clave in destino:
                    raise ValueError(f"Clave i18n duplicada detectada: {clave}")
                destino[clave] = valor
    return catalogo_final


_TRANSLATIONS = _merge_catalogos_sin_duplicados(
    I18N_CATALOGO_CORE,
    I18N_CATALOGO_UX,
    I18N_CATALOGO_PREDICCION,
    PREDICCION_RESULTADOS_TRANSLATIONS,
    RECORDATORIO_TRANSLATIONS,
    PREDICCION_RECORDATORIO_TRANSLATIONS,
    ML_OPERATIVA_TRANSLATIONS,
)
