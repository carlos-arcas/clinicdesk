from __future__ import annotations

from clinicdesk.app.application.usecases.obtener_resumen_telemetria_semana import ObtenerResumenTelemetriaSemana
from clinicdesk.app.queries.telemetria_eventos_queries import TopEventoTelemetriaQuery


class _GatewayFake:
    def top_eventos_por_rango(self, desde_utc, hasta_utc, limit: int = 5):
        assert limit == 5
        return [
            TopEventoTelemetriaQuery(evento="gestion_abrir_cita", total=4),
            TopEventoTelemetriaQuery(evento="auditoria_export", total=2),
        ]


def test_obtener_resumen_telemetria_semana_mapea_top_eventos() -> None:
    uc = ObtenerResumenTelemetriaSemana(_GatewayFake())

    resumen = uc.ejecutar()

    assert len(resumen.top_eventos) == 2
    assert resumen.top_eventos[0].evento == "gestion_abrir_cita"
    assert resumen.top_eventos[0].total == 4
