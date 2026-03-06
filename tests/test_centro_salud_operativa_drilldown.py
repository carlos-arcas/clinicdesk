from __future__ import annotations

from datetime import date

from clinicdesk.app.application.usecases.centro_salud_operativa import AlertaCentroSaludDTO, FiltrosCentroSaludDTO
from clinicdesk.app.application.usecases.centro_salud_operativa_drilldown import (
    construir_accion_alerta,
    construir_acciones_kpi,
)


def _filtros() -> FiltrosCentroSaludDTO:
    return FiltrosCentroSaludDTO(desde=date(2025, 1, 2), hasta=date(2025, 1, 5))


def test_kpis_drilldown_construye_intents_contextuales() -> None:
    acciones = construir_acciones_kpi(_filtros(), riesgo_disponible=True)

    assert [item.clave for item in acciones] == [
        "pendientes",
        "canceladas_no_show",
        "tasa_no_asistencia",
        "riesgo",
    ]
    assert acciones[0].intent_citas is not None
    assert acciones[0].intent_citas.estado_cita == "PROGRAMADA"
    assert acciones[1].intent_citas is not None
    assert acciones[1].intent_citas.estado_cita == "CANCELADA"
    assert acciones[2].intent_citas is not None
    assert acciones[2].intent_citas.estado_cita == "NO_PRESENTADO"
    assert acciones[3].intent_citas is not None
    assert acciones[3].intent_citas.incluir_riesgo is True


def test_kpi_riesgo_sin_fuente_se_marca_no_disponible() -> None:
    accion = construir_acciones_kpi(_filtros(), riesgo_disponible=False)[3]

    assert accion.clave == "riesgo"
    assert accion.disponible is False
    assert accion.motivo_no_disponible_i18n_key == "dashboard_gestion.operativa.drilldown.sin_destino.riesgo"


def test_alerta_cuellos_navega_a_confirmaciones() -> None:
    accion = construir_accion_alerta(
        AlertaCentroSaludDTO(
            severidad="MEDIA",
            i18n_key="dashboard_gestion.operativa.alerta.cuellos",
            total=3,
        ),
        _filtros(),
    )

    assert accion.destino == "confirmaciones"
    assert accion.intent_citas is None


def test_alerta_pacientes_riesgo_sin_destino_directo() -> None:
    accion = construir_accion_alerta(
        AlertaCentroSaludDTO(
            severidad="MEDIA",
            i18n_key="dashboard_gestion.operativa.alerta.pacientes_riesgo",
            total=2,
        ),
        _filtros(),
    )

    assert accion.disponible is False
    assert accion.motivo_no_disponible_i18n_key == "dashboard_gestion.operativa.drilldown.sin_destino.paciente"
