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
from clinicdesk.app.application.usecases.preflight_integridad_auditoria import (
    EstadoIntegridadAuditoria,
    IntegridadAuditoriaComprometidaError,
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


def test_exportar_auditoria_csv_redacta_pii_historica() -> None:
    rows = [
        AuditoriaAccesoItemQuery(
            timestamp_utc="2026-01-01T08:00:00+00:00",
            usuario="paciente@example.com",
            modo_demo=False,
            accion="VER_HISTORIAL_PACIENTE",
            entidad_tipo="PACIENTE",
            entidad_id="historia clinica HC-77881, dni=12345678Z",
        )
    ]
    usecase = ExportarAuditoriaCSV(GatewayFake(total=1, rows=rows))

    dto = usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))

    assert "paciente@example.com" not in dto.csv_texto
    assert "12345678Z" not in dto.csv_texto
    assert "HC-77881" not in dto.csv_texto
    assert "[REDACTED_EMAIL]" in dto.csv_texto
    assert "[REDACTED_DNI_NIF]" in dto.csv_texto
    assert "[REDACTED_HISTORIA_CLINICA]" in dto.csv_texto


def test_exportar_auditoria_csv_redacta_estructuras_anidadas_en_serializacion() -> None:
    rows = [
        {
            "timestamp_utc": "2026-01-01T08:00:00+00:00",
            "usuario": "ana",
            "modo_demo": False,
            "accion": "VER_HISTORIAL_PACIENTE",
            "entidad_tipo": "PACIENTE",
            "entidad_id": {
                "historia_clinica": "HC-999",
                "extra": {"telefono": "+34 600 111 222", "detalle": "ok"},
            },
        }
    ]
    usecase = ExportarAuditoriaCSV(GatewayFake(total=1, rows=rows))

    dto = usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))

    assert "HC-999" not in dto.csv_texto
    assert "+34 600 111 222" not in dto.csv_texto
    assert "[REDACTED_FIELD]" in dto.csv_texto


class VerificadorIntegridadFake:
    def __init__(self, resultado: EstadoIntegridadAuditoria) -> None:
        self.resultado = resultado
        self.llamadas = 0

    def verificar_integridad_auditoria(self) -> EstadoIntegridadAuditoria:
        self.llamadas += 1
        return self.resultado


def test_exportar_auditoria_csv_ejecuta_preflight_integridad() -> None:
    verificador = VerificadorIntegridadFake(EstadoIntegridadAuditoria(ok=True))
    usecase = ExportarAuditoriaCSV(
        GatewayFake(total=1, rows=[]),
        verificador_integridad=verificador,
    )

    usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))

    assert verificador.llamadas == 1


def test_exportar_auditoria_csv_bloquea_si_cadena_comprometida() -> None:
    verificador = VerificadorIntegridadFake(
        EstadoIntegridadAuditoria(ok=False, tabla="auditoria_accesos", primer_fallo_id=3)
    )
    usecase = ExportarAuditoriaCSV(
        GatewayFake(total=1, rows=[]),
        verificador_integridad=verificador,
    )

    with pytest.raises(IntegridadAuditoriaComprometidaError) as excinfo:
        usecase.execute(FiltrosAuditoriaAccesos(accion="VER_DETALLE_CITA"))

    assert excinfo.value.reason_code == "auditoria_integridad_comprometida"
    assert excinfo.value.tabla == "auditoria_accesos"
    assert excinfo.value.primer_fallo_id == 3
