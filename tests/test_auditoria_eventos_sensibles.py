from __future__ import annotations

import json

import pytest

from clinicdesk.app.application.auditoria.audit_service import (
    AuditEvent,
    AuditMetadataError,
    AuditService,
)
from clinicdesk.app.application.security import AutorizadorAcciones, Role, UserContext
from clinicdesk.app.application.usecases.crear_cita import CrearCitaRequest, CrearCitaUseCase
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData, SeedDemoDataRequest
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.exceptions import AuthorizationError


class RepositorioAuditoriaFake:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)


class SeederDummy:
    class _Resultado:
        doctors = 1
        patients = 2
        personal = 1
        appointments = 3
        incidences = 1
        medicamentos = 0
        materiales = 0
        recetas = 0
        receta_lineas = 0
        dispensaciones = 0
        movimientos_medicamentos = 0
        movimientos_materiales = 0
        turnos = 0
        ausencias = 0

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def persist(self, *args, **kwargs):
        if self.fail:
            raise RuntimeError("forced")
        return self._Resultado()


def test_seed_demo_guarda_auditoria_ok_y_fail_en_repo_fake() -> None:
    repo = RepositorioAuditoriaFake()
    service = AuditService(repo)
    user = UserContext(role=Role.ADMIN, username="admin", run_id="run-seed")

    seed_ok = SeedDemoData(
        SeederDummy(fail=False),
        user_context=user,
        autorizador_acciones=AutorizadorAcciones(),
        audit_service=service,
    )
    response = seed_ok.execute(SeedDemoDataRequest(seed=55, n_doctors=1, n_patients=2, n_appointments=3))
    assert response.appointments == 3

    seed_fail = SeedDemoData(
        SeederDummy(fail=True),
        user_context=user,
        autorizador_acciones=AutorizadorAcciones(),
        audit_service=service,
    )
    with pytest.raises(RuntimeError):
        seed_fail.execute(SeedDemoDataRequest(seed=99, n_doctors=1, n_patients=2, n_appointments=3))

    assert [e.action for e in repo.events] == ["DEMO_SEED", "DEMO_SEED"]
    assert [e.outcome for e in repo.events] == ["ok", "fail"]


def test_audit_service_redacta_pii_en_valores() -> None:
    repo = RepositorioAuditoriaFake()
    service = AuditService(repo)

    event = service.registrar(
        action="CITA_CREAR",
        outcome="ok",
        actor_username="admin",
        actor_role=Role.ADMIN,
        correlation_id="run-1",
        metadata={
            "error_code": "usuario=ana@test.com dni=12345678Z telefono=600123123",
            "medico_id": 7,
        },
    )

    assert event.metadata["error_code"] == "usuario=[REDACTED_EMAIL] dni=[REDACTED_DNI_NIF] telefono=[REDACTED_PHONE]"


def test_audit_service_falla_si_key_no_permitida() -> None:
    repo = RepositorioAuditoriaFake()
    service = AuditService(repo)

    with pytest.raises(AuditMetadataError, match="no permitida"):
        service.registrar(
            action="CITA_CREAR",
            outcome="ok",
            actor_username="admin",
            actor_role=Role.ADMIN,
            correlation_id=None,
            metadata={"email": "ana@test.com"},
        )


def test_crear_cita_admin_registra_auditoria_ok(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)
    req = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-20 10:00:00",
        fin="2024-05-20 10:20:00",
        motivo="Control",
        estado=EstadoCita.PROGRAMADA.value,
    )

    result = usecase.execute(req)

    assert result.cita_id > 0
    audit_row = container.connection.execute(
        "SELECT action, outcome, actor_role, metadata_json FROM auditoria_eventos ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert audit_row is not None
    assert audit_row["action"] == "CITA_CREAR"
    assert audit_row["outcome"] == "ok"
    assert audit_row["actor_role"] == Role.ADMIN.value
    metadata = json.loads(audit_row["metadata_json"] or "{}")
    assert "paciente_id" not in metadata


def test_crear_cita_readonly_falla_y_registra_auditoria_fail(container, seed_data) -> None:
    container.user_context.role = Role.READONLY
    usecase = CrearCitaUseCase(container)
    req = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-20 11:00:00",
        fin="2024-05-20 11:20:00",
        motivo="Control",
        estado=EstadoCita.PROGRAMADA.value,
    )

    with pytest.raises(AuthorizationError):
        usecase.execute(req)

    audit_row = container.connection.execute(
        "SELECT action, outcome, actor_role, metadata_json FROM auditoria_eventos ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert audit_row is not None
    assert audit_row["action"] == "CITA_CREAR"
    assert audit_row["outcome"] == "fail"
    assert audit_row["actor_role"] == Role.READONLY.value
    assert "AuthorizationError" in (audit_row["metadata_json"] or "")
