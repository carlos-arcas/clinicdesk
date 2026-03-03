from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
from typing import Protocol

from clinicdesk.app.application.usecases.filtros_auditoria import aplicar_preset_rango_auditoria
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesoItemQuery, FiltrosAuditoriaAccesos


class ExportacionAuditoriaDemasiadasFilasError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExportacionCSVDTO:
    nombre_archivo_sugerido: str
    csv_texto: str
    filas: int


class ExportarAuditoriaCSVGateway(Protocol):
    def buscar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditoriaAccesoItemQuery], int]:
        ...

    def exportar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        max_filas: int | None = None,
    ) -> list[AuditoriaAccesoItemQuery]:
        ...


class ExportarAuditoriaCSV:
    _MAX_FILAS_DEFENSIVO = 10_000

    def __init__(self, gateway: ExportarAuditoriaCSVGateway) -> None:
        self._gateway = gateway

    def execute(self, filtros: FiltrosAuditoriaAccesos, preset_rango: str | None = None) -> ExportacionCSVDTO:
        filtros_finales = aplicar_preset_rango_auditoria(filtros, preset_rango)
        _, total = self._gateway.buscar_auditoria_accesos(filtros_finales, limit=1, offset=0)
        if total > self._MAX_FILAS_DEFENSIVO:
            raise ExportacionAuditoriaDemasiadasFilasError("Demasiadas filas, acota el rango")
        filas = self._gateway.exportar_auditoria_accesos(filtros_finales, max_filas=self._MAX_FILAS_DEFENSIVO)
        return ExportacionCSVDTO(
            nombre_archivo_sugerido=_build_file_name(),
            csv_texto=_render_csv(filas),
            filas=len(filas),
        )


def _build_file_name() -> str:
    return f"auditoria_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"


def _render_csv(filas: list[AuditoriaAccesoItemQuery]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "usuario", "demo", "accion", "entidad_tipo", "entidad_id"])
    for item in filas:
        writer.writerow([item.timestamp_utc, item.usuario, str(item.modo_demo), item.accion, item.entidad_tipo, item.entidad_id])
    return output.getvalue()
