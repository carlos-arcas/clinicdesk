from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.application.usecases.filtros_auditoria import (
    aplicar_preset_rango_auditoria,
    redactar_texto_filtro_auditoria,
)
from clinicdesk.app.application.usecases.preflight_integridad_auditoria import (
    VerificadorIntegridadAuditoriaGateway,
    exigir_integridad_auditoria,
)
from clinicdesk.app.queries.auditoria_accesos_queries import (
    AuditoriaAccesoItemQuery,
    FiltrosAuditoriaAccesos,
)


LOGGER = get_logger(__name__)


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
        *,
        calcular_total: bool = True,
    ) -> tuple[list[AuditoriaAccesoItemQuery], int | None]: ...


class BuscarAuditoriaAccesos:
    def __init__(
        self,
        gateway: BuscarAuditoriaAccesosGateway,
        *,
        verificador_integridad: VerificadorIntegridadAuditoriaGateway | None = None,
    ) -> None:
        self._gateway = gateway
        self._verificador_integridad = verificador_integridad

    def execute(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
        preset_rango: str | None = None,
        total_conocido: int | None = None,
    ) -> ResultadoAuditoriaAccesosDTO:
        exigir_integridad_auditoria(self._verificador_integridad)
        filtros_finales = aplicar_preset_rango_auditoria(filtros, preset_rango)
        debe_calcular_total = total_conocido is None
        items, total = self._gateway.buscar_auditoria_accesos(
            filtros_finales,
            limit,
            offset,
            calcular_total=debe_calcular_total,
        )
        LOGGER.info(
            "auditoria_filtros_aplicados",
            extra=_payload_log_filtros_auditoria(filtros_finales, "auditoria_filtros_aplicados"),
        )
        filas = tuple(self._map_item(item) for item in items)
        total_final = total if total is not None else (total_conocido or 0)
        return ResultadoAuditoriaAccesosDTO(total=total_final, items=filas)

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


def _payload_log_filtros_auditoria(filtros: FiltrosAuditoriaAccesos, accion: str) -> dict[str, object]:
    return {
        "action": accion,
        "usuario_contiene": redactar_texto_filtro_auditoria(filtros.usuario_contiene),
        "filtro_accion": filtros.accion,
        "filtro_entidad_tipo": filtros.entidad_tipo,
    }
