from clinicdesk.app.application.prediccion_operativa.dtos import ExplicacionOperativaDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.prediccion_operativa.helpers import (
    construir_bullets_explicacion,
    debe_cargar_previsualizacion,
    resolver_clave_estado_salud,
)


def test_resolver_clave_estado_salud_no_tech() -> None:
    assert resolver_clave_estado_salud("VERDE") == "prediccion_operativa.estado.bien"
    assert resolver_clave_estado_salud("AMARILLO") == "prediccion_operativa.estado.atencion"
    assert resolver_clave_estado_salud("OTRO") == "prediccion_operativa.estado.no_disponible"


def test_construir_bullets_desde_reason_codes() -> None:
    dto = ExplicacionOperativaDTO(
        nivel="ALTO",
        motivos_i18n_keys=(
            "citas.prediccion_operativa.motivo.franja_demanda",
            "citas.prediccion_operativa.motivo.referencia_general",
        ),
        acciones_i18n_keys=(),
        necesita_entrenar=False,
    )
    texto = construir_bullets_explicacion(dto, I18nManager("es"))
    assert "• Esta franja suele tener más espera." in texto
    assert "• Estimación basada en referencia general." in texto


def test_toggle_off_no_carga_preview() -> None:
    assert debe_cargar_previsualizacion(True) is True
    assert debe_cargar_previsualizacion(False) is False


def test_construir_bullets_fallback_no_disponible() -> None:
    dto = ExplicacionOperativaDTO(
        nivel="NO_DISPONIBLE", motivos_i18n_keys=(), acciones_i18n_keys=(), necesita_entrenar=True
    )
    texto = construir_bullets_explicacion(dto, I18nManager("es"))
    assert "• No disponible." in texto
