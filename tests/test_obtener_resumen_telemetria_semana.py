from __future__ import annotations

import pytest

from clinicdesk.app.application.usecases.obtener_resumen_telemetria_semana import ObtenerResumenTelemetriaSemana
from clinicdesk.app.application.usecases.preflight_integridad_telemetria import (
    EstadoIntegridadTelemetria,
    IntegridadTelemetriaComprometidaError,
)
from clinicdesk.app.queries.telemetria_eventos_queries import TopEventoTelemetriaQuery


class _GatewayFake:
    def top_eventos_por_rango(self, desde_utc, hasta_utc, limit: int = 5):
        assert limit == 5
        return [
            TopEventoTelemetriaQuery(evento="gestion_abrir_cita", total=4),
            TopEventoTelemetriaQuery(evento="auditoria_export", total=2),
        ]


class _VerificadorOk:
    def verificar_integridad_telemetria(self) -> EstadoIntegridadTelemetria:
        return EstadoIntegridadTelemetria(ok=True)


class _VerificadorRoto:
    def verificar_integridad_telemetria(self) -> EstadoIntegridadTelemetria:
        return EstadoIntegridadTelemetria(ok=False, tabla="telemetria_eventos", primer_fallo_id=3)


def test_obtener_resumen_telemetria_semana_mapea_top_eventos() -> None:
    uc = ObtenerResumenTelemetriaSemana(_GatewayFake(), verificador_integridad=_VerificadorOk())

    resumen = uc.ejecutar()

    assert len(resumen.top_eventos) == 2
    assert resumen.top_eventos[0].evento == "gestion_abrir_cita"
    assert resumen.top_eventos[0].total == 4


def test_obtener_resumen_telemetria_semana_falla_si_integridad_comprometida() -> None:
    uc = ObtenerResumenTelemetriaSemana(_GatewayFake(), verificador_integridad=_VerificadorRoto())

    with pytest.raises(IntegridadTelemetriaComprometidaError) as exc:
        uc.ejecutar()

    assert exc.value.reason_code == "telemetria_integridad_comprometida"
    assert exc.value.tabla == "telemetria_eventos"
    assert exc.value.primer_fallo_id == 3
