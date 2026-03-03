from __future__ import annotations

from datetime import date

import pytest

from clinicdesk.app.application.usecases.dashboard_gestion import (
    FiltrosDashboardDTO,
    ObtenerDashboardGestion,
    UMBRAL_ALERTA_ESPERA_ALTA_MIN,
    UMBRAL_ALERTA_POCOS_DATOS_ESPERA,
    UMBRAL_ALERTA_RETRASO_ALTO_MIN,
    normalizar_filtros_dashboard,
)
from clinicdesk.app.application.usecases.obtener_metricas_operativas import KpiDiaDTO, KpiMedicoDTO, ResultadoMetricasOperativasDTO
from clinicdesk.app.domain.exceptions import ValidationError


class _FakeMetricas:
    def __init__(self, resultado: ResultadoMetricasOperativasDTO) -> None:
        self._resultado = resultado
        self.last_desde: date | None = None
        self.last_hasta: date | None = None

    def execute(self, desde: date, hasta: date) -> ResultadoMetricasOperativasDTO:
        self.last_desde = desde
        self.last_hasta = hasta
        return self._resultado


def test_normalizar_filtros_dashboard_aplica_preset_7_dias() -> None:
    resultado = normalizar_filtros_dashboard(FiltrosDashboardDTO(preset="bad"), date(2025, 1, 31))

    assert resultado.preset == "7_DIAS"
    assert resultado.desde == date(2025, 1, 25)
    assert resultado.hasta == date(2025, 1, 31)


def test_normalizar_filtros_dashboard_personalizado_ordenado() -> None:
    resultado = normalizar_filtros_dashboard(
        FiltrosDashboardDTO(preset="PERSONALIZADO", desde=date(2025, 2, 5), hasta=date(2025, 2, 1)),
        date(2025, 2, 10),
    )

    assert resultado.desde == date(2025, 2, 1)
    assert resultado.hasta == date(2025, 2, 5)


def test_normalizar_filtros_dashboard_valida_rango_maximo() -> None:
    with pytest.raises(ValidationError):
        normalizar_filtros_dashboard(
            FiltrosDashboardDTO(preset="PERSONALIZADO", desde=date(2025, 1, 1), hasta=date(2025, 4, 5)),
            date(2025, 4, 5),
        )


def test_use_case_dashboard_deriva_top_y_alertas() -> None:
    fake = _FakeMetricas(_resultado_metricas(espera=20.0, retraso=12.0, total_validas_espera=10))
    use_case = ObtenerDashboardGestion(fake)

    resultado = use_case.execute(FiltrosDashboardDTO(preset="HOY"), hoy=date(2025, 1, 10))

    assert fake.last_desde == date(2025, 1, 10)
    assert resultado.kpis_resumen.total_citas == 15
    assert resultado.kpis_resumen.espera_media_min == 20.0
    assert len(resultado.top_medicos) == 5
    assert resultado.top_medicos[0].medico_nombre == "Medico C"
    codigos = {alerta.code for alerta in resultado.alertas}
    assert codigos == {"espera_alta", "retraso_alto", "pocos_datos"}


def test_alertas_respetan_umbrales_estrictos() -> None:
    fake = _FakeMetricas(
        _resultado_metricas(
            espera=UMBRAL_ALERTA_ESPERA_ALTA_MIN,
            retraso=UMBRAL_ALERTA_RETRASO_ALTO_MIN,
            total_validas_espera=UMBRAL_ALERTA_POCOS_DATOS_ESPERA,
        )
    )
    use_case = ObtenerDashboardGestion(fake)

    resultado = use_case.execute(FiltrosDashboardDTO(preset="HOY"), hoy=date(2025, 1, 10))

    assert resultado.alertas == ()


def _resultado_metricas(espera: float, retraso: float, total_validas_espera: int) -> ResultadoMetricasOperativasDTO:
    por_dia = (
        KpiDiaDTO(
            fecha="2025-01-10",
            total_citas=15,
            total_validas_espera=total_validas_espera,
            espera_media_min=espera,
            total_validas_consulta=10,
            consulta_media_min=25.0,
            total_clinica_media_min=40.0,
            total_validas_retraso=8,
            retraso_media_min=retraso,
            descartados=0,
        ),
    )
    por_medico = (
        KpiMedicoDTO(1, "Medico A", 3, 8.0, 20.0, 2.0),
        KpiMedicoDTO(2, "Medico B", 2, 7.0, 18.0, 1.0),
        KpiMedicoDTO(3, "Medico C", 5, 10.0, 22.0, 3.0),
        KpiMedicoDTO(4, "Medico D", 1, 6.0, 17.0, 0.5),
        KpiMedicoDTO(5, "Medico E", 2, 6.5, 16.0, 0.5),
        KpiMedicoDTO(6, "Medico F", 2, 7.5, 19.0, 1.5),
    )
    return ResultadoMetricasOperativasDTO(desde="2025-01-10", hasta="2025-01-10", por_dia=por_dia, por_medico=por_medico)
