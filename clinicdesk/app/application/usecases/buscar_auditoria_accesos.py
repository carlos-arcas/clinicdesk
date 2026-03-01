from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.queries.auditoria_accesos_queries import (
    AuditoriaAccesoItemQuery,
    FiltrosAuditoriaAccesos,
)


@dataclass(frozen=True, slots=True)
class AuditoriaAccesoFilaDTO:
    timestamp_utc: str
    usuario: str
    modo_demo: bool
    accion: str
    entidad_tipo: str
    entidad_id: str


@dataclass(frozen=True, slots=True)
class ResultadoAuditoriaAccesosDTO:
    total: int
    items: tuple[AuditoriaAccesoFilaDTO, ...]


class BuscarAuditoriaAccesosGateway(Protocol):
    def buscar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditoriaAccesoItemQuery], int]:
        ...


class BuscarAuditoriaAccesos:
    def __init__(self, gateway: BuscarAuditoriaAccesosGateway) -> None:
        self._gateway = gateway

    def execute(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
    ) -> ResultadoAuditoriaAccesosDTO:
        items, total = self._gateway.buscar_auditoria_accesos(filtros, limit, offset)
        filas = tuple(self._map_item(item) for item in items)
        return ResultadoAuditoriaAccesosDTO(total=total, items=filas)

    @staticmethod
    def _map_item(item: AuditoriaAccesoItemQuery) -> AuditoriaAccesoFilaDTO:
        return AuditoriaAccesoFilaDTO(
            timestamp_utc=item.timestamp_utc,
            usuario=item.usuario,
            modo_demo=item.modo_demo,
            accion=item.accion,
            entidad_tipo=item.entidad_tipo,
            entidad_id=item.entidad_id,
        )
