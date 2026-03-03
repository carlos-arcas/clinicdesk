from __future__ import annotations

import csv
from io import StringIO

import pytest

from clinicdesk.app.application.usecases.exportar_auditoria_csv import (
    ExportacionAuditoriaDemasiadasFilasError,
    ExportarAuditoriaCSV,
)
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesoItemQuery, FiltrosAuditoriaAccesos


class GatewayFake:
    def __init__(self, total: int, rows: list[AuditoriaAccesoItemQuery]) -> None:
        self.total = total
        self.rows = rows

    def buscar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditoriaAccesoItemQuery], int]:
        assert filtros.accion == "VER_DETALLE_CITA"
        return self.rows[:limit], self.total

    def exportar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        max_filas: int | None = None,
    ) -> list[AuditoriaAccesoItemQuery]:
        assert max_filas == 10_000
        return self.rows


def test_exportar_auditoria_csv_genera_cabeceras_y_sin_metadata() -> None:
    rows = [
        AuditoriaAccesoItemQuery(
            timestamp_utc="2026-01-01T08:00:00+00:00",
            usuario="ana",
            modo_demo=False,
            accion="VER_DETALLE_CITA",
            entidad_tipo="CITA",
            entidad_id="10",
        )
    ]
    usecase = ExportarAuditoriaCSV(GatewayFake(total=1, rows=rows))

    dto = usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))
    data = list(csv.reader(StringIO(dto.csv_texto)))

    assert data[0] == ["timestamp", "usuario", "demo", "accion", "entidad_tipo", "entidad_id"]
    assert "metadata_json" not in dto.csv_texto
    assert data[1][1] == "ana"


def test_exportar_auditoria_csv_limite_defensivo() -> None:
    usecase = ExportarAuditoriaCSV(GatewayFake(total=10_001, rows=[]))

    with pytest.raises(ExportacionAuditoriaDemasiadasFilasError):
        usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))
