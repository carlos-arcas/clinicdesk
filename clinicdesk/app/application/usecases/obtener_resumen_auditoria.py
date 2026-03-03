from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Protocol

from clinicdesk.app.queries.auditoria_accesos_queries import TopAccionAuditoriaQuery


@dataclass(frozen=True, slots=True)
class TopAccionResumenAuditoriaDTO:
    accion: str
    total: int


@dataclass(frozen=True, slots=True)
class ResumenAuditoriaDTO:
    accesos_hoy: int
    accesos_ultimos_7_dias: int
    top_acciones: tuple[TopAccionResumenAuditoriaDTO, ...]


class ObtenerResumenAuditoriaGateway(Protocol):
    def contar_accesos_por_rango(
        self,
        desde_utc: str | datetime | None,
        hasta_utc: str | datetime | None,
    ) -> int:
        ...

    def top_acciones_por_rango(
        self,
        desde_utc: str | datetime | None,
        hasta_utc: str | datetime | None,
        limit: int = 3,
    ) -> list[TopAccionAuditoriaQuery]:
        ...


class ObtenerResumenAuditoria:
    def __init__(self, gateway: ObtenerResumenAuditoriaGateway) -> None:
        self._gateway = gateway

    def execute(
        self,
        desde_utc: str | datetime | None,
        hasta_utc: str | datetime | None,
    ) -> ResumenAuditoriaDTO:
        desde_hoy, hasta_hoy = _rango_hoy_utc()
        desde_7 = desde_hoy - timedelta(days=6)
        return ResumenAuditoriaDTO(
            accesos_hoy=self._gateway.contar_accesos_por_rango(desde_hoy, hasta_hoy),
            accesos_ultimos_7_dias=self._gateway.contar_accesos_por_rango(desde_7, hasta_hoy),
            top_acciones=tuple(
                TopAccionResumenAuditoriaDTO(accion=item.accion, total=item.total)
                for item in self._gateway.top_acciones_por_rango(desde_utc, hasta_utc, limit=3)
            ),
        )


def _rango_hoy_utc() -> tuple[datetime, datetime]:
    ahora = datetime.now(UTC)
    desde = datetime.combine(ahora.date(), time.min, tzinfo=UTC)
    hasta = datetime.combine(ahora.date(), time.max, tzinfo=UTC)
    return desde, hasta
