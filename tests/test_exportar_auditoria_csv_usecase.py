from __future__ import annotations

import csv
from io import StringIO
from typing import Any

import pytest

from clinicdesk.app.application.auditoria.audit_service import AuditEvent, AuditService
from clinicdesk.app.application.security import AutorizadorAcciones, Role, UserContext
from clinicdesk.app.application.usecases.exportar_auditoria_csv import (
    COLUMNAS_EXPORTACION_AUDITORIA,
    ExportacionAuditoriaDemasiadasFilasError,
    ExportacionAuditoriaError,
    ExportarAuditoriaCSV,
)
from clinicdesk.app.domain.exceptions import AuthorizationError
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesoItemQuery, FiltrosAuditoriaAccesos


class GatewayFake:
    def __init__(self, total: int, rows: list[AuditoriaAccesoItemQuery | dict[str, Any]]) -> None:
        self.total = total
        self.rows = rows

    def buscar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditoriaAccesoItemQuery | dict[str, Any]], int]:
        assert filtros.accion == "VER_DETALLE_CITA"
        return self.rows[:limit], self.total

    def exportar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        max_filas: int | None = None,
    ) -> list[AuditoriaAccesoItemQuery | dict[str, Any]]:
        assert max_filas == 10_000
        return self.rows


class _RepoAuditoriaFake:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)


def test_exportar_auditoria_csv_solo_serializa_columnas_permitidas() -> None:
    rows = [
        {
            "timestamp_utc": "2026-01-01T08:00:00+00:00",
            "usuario": "ana",
            "modo_demo": False,
            "accion": "VER_DETALLE_CITA",
            "entidad_tipo": "CITA",
            "entidad_id": "10",
            "metadata_json": '{"ssn":"123"}',
            "campo_interno": "secreto",
        }
    ]
    usecase = ExportarAuditoriaCSV(GatewayFake(total=1, rows=rows))

    dto = usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))
    data = list(csv.reader(StringIO(dto.csv_texto)))

    assert data[0] == list(COLUMNAS_EXPORTACION_AUDITORIA)
    assert "metadata_json" not in dto.csv_texto
    assert '{"ssn":"123"}' not in dto.csv_texto
    assert "campo_interno" not in dto.csv_texto


def test_exportar_auditoria_csv_headers_exactos_y_ordenados() -> None:
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

    assert tuple(data[0]) == COLUMNAS_EXPORTACION_AUDITORIA


def test_exportar_auditoria_csv_limite_defensivo() -> None:
    usecase = ExportarAuditoriaCSV(GatewayFake(total=10_001, rows=[]))

    with pytest.raises(ExportacionAuditoriaDemasiadasFilasError):
        usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))


def test_exportar_auditoria_csv_exige_rbac_y_audita_fail() -> None:
    repo = _RepoAuditoriaFake()
    usecase = ExportarAuditoriaCSV(
        GatewayFake(total=1, rows=[]),
        user_context=UserContext(role=Role.READONLY, username="readonly"),
        autorizador_acciones=AutorizadorAcciones(),
        audit_service=AuditService(repo),
    )

    with pytest.raises(AuthorizationError):
        usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))

    assert repo.events[-1].outcome == "fail"


def test_exportar_auditoria_csv_pii_requiere_confirmacion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLINICDESK_EXPORT_PII", "1")
    repo = _RepoAuditoriaFake()
    usecase = ExportarAuditoriaCSV(
        GatewayFake(total=1, rows=[]),
        user_context=UserContext(role=Role.ADMIN, username="admin"),
        autorizador_acciones=AutorizadorAcciones(),
        audit_service=AuditService(repo),
    )

    with pytest.raises(ExportacionAuditoriaError, match="confirmation_required"):
        usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"), incluir_pii=True)

    assert repo.events[-1].metadata["reason_code"] == "confirmation_required"
