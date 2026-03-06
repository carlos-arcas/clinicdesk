from __future__ import annotations

from clinicdesk.app.application.usecases.centro_salud_operativa import (
    AlertaCentroSaludDTO,
    CentroSaludOperativaDTO,
    KpiCentroSaludDTO,
)
from clinicdesk.app.application.usecases.exportar_centro_salud_operativa_csv import exportar_centro_salud_operativa_csv


def test_exportar_centro_salud_operativa_csv_incluye_kpis_y_alertas() -> None:
    data = CentroSaludOperativaDTO(
        kpis=KpiCentroSaludDTO(
            total_citas=40,
            completadas=25,
            pendientes=10,
            canceladas_no_show=5,
            no_show=3,
            tasa_no_asistencia_pct=7.5,
            riesgo_medio_pct=55.4,
        ),
        alertas=(AlertaCentroSaludDTO(severidad="ALTA", i18n_key="dashboard_gestion.operativa.alerta.riesgo_alto", total=2),),
    )

    contenido = exportar_centro_salud_operativa_csv(data)

    assert "total_citas,40" in contenido
    assert "tasa_no_asistencia_pct,7.50" in contenido
    assert "ALTA,dashboard_gestion.operativa.alerta.riesgo_alto,2" in contenido
