from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Protocol

from clinicdesk.app.queries.telemetria_eventos_queries import TopEventoTelemetriaQuery


@dataclass(frozen=True, slots=True)
class EventoResumenTelemetriaDTO:
    evento: str
    total: int


@dataclass(frozen=True, slots=True)
class ResumenTelemetriaSemanaDTO:
    top_eventos: tuple[EventoResumenTelemetriaDTO, ...]


class ObtenerResumenTelemetriaSemanaGateway(Protocol):
    def top_eventos_por_rango(
        self,
        desde_utc: str | datetime,
        hasta_utc: str | datetime,
        limit: int = 5,
    ) -> list[TopEventoTelemetriaQuery]: ...


class ObtenerResumenTelemetriaSemana:
    def __init__(self, gateway: ObtenerResumenTelemetriaSemanaGateway) -> None:
        self._gateway = gateway

    def ejecutar(self) -> ResumenTelemetriaSemanaDTO:
        desde, hasta = _rango_ultimos_7_dias_utc()
        top_eventos = self._gateway.top_eventos_por_rango(desde, hasta, limit=5)
        return ResumenTelemetriaSemanaDTO(
            top_eventos=tuple(EventoResumenTelemetriaDTO(evento=item.evento, total=item.total) for item in top_eventos)
        )


def _rango_ultimos_7_dias_utc() -> tuple[datetime, datetime]:
    ahora = datetime.now(UTC)
    hasta = datetime.combine(ahora.date(), time.max, tzinfo=UTC)
    desde = datetime.combine((ahora - timedelta(days=6)).date(), time.min, tzinfo=UTC)
    return desde, hasta
