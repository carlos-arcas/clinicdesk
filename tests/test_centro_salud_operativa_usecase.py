from __future__ import annotations

from datetime import date

from clinicdesk.app.application.usecases.centro_salud_operativa import (
    FiltrosCentroSaludDTO,
    ObtenerCentroSaludOperativa,
)


class _FakeQueries:
    def __init__(self, total_riesgo_alto: int = 0, pacientes: int = 0, cuellos: int = 0) -> None:
        self.total_riesgo_alto = total_riesgo_alto
        self.pacientes = pacientes
        self.cuellos = cuellos

    def obtener_resumen_centro_salud(self, desde, hasta, medico_id, sala_id, estado):
        class _Row:
            total_citas = 20
            total_completadas = 12
            total_pendientes = 4
            total_canceladas = 4
            total_no_presentadas = 3
            riesgo_medio_pct = 67.89
            total_riesgo_alto = self.total_riesgo_alto

        return _Row()

    def contar_pacientes_riesgo_operativo(self, desde: date, hasta: date) -> int:
        return self.pacientes

    def contar_cuellos_botella(self, desde: date, hasta: date, medico_id: int | None, sala_id: int | None) -> int:
        return self.cuellos


def test_centro_salud_deriva_kpis_y_alertas() -> None:
    use_case = ObtenerCentroSaludOperativa(_FakeQueries(total_riesgo_alto=2, pacientes=1, cuellos=3))

    resultado = use_case.execute(FiltrosCentroSaludDTO(desde=date(2025, 1, 1), hasta=date(2025, 1, 31)))

    assert resultado.kpis.total_citas == 20
    assert resultado.kpis.tasa_no_asistencia_pct == 15.0
    assert [item.i18n_key for item in resultado.alertas] == [
        "dashboard_gestion.operativa.alerta.riesgo_alto",
        "dashboard_gestion.operativa.alerta.pacientes_riesgo",
        "dashboard_gestion.operativa.alerta.cuellos",
    ]


def test_centro_salud_reporta_estado_estable_sin_alertas() -> None:
    use_case = ObtenerCentroSaludOperativa(_FakeQueries())

    resultado = use_case.execute(FiltrosCentroSaludDTO(desde=date(2025, 1, 1), hasta=date(2025, 1, 1)))

    assert resultado.alertas[0].i18n_key == "dashboard_gestion.operativa.alerta.sin_alertas"
