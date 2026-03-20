from __future__ import annotations

import json

import pytest

from clinicdesk.app.application.security import Role
from clinicdesk.app.application.usecases.crear_cita import (
    CrearCitaRequest,
    CrearCitaUseCase,
    PendingWarningsError,
)
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.exceptions import AuthorizationError, ValidationError


class _RepoSpy:
    def __init__(self, original) -> None:
        self._original = original
        self.calls = 0

    def create(self, *args, **kwargs):
        self.calls += 1
        return self._original.create(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(self._original, name)


@pytest.fixture()
def request_base(seed_data) -> CrearCitaRequest:
    return CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-20 15:00:00",
        fin="2024-05-20 15:20:00",
        motivo="Control de seguridad",
        estado=EstadoCita.PROGRAMADA.value,
    )


@pytest.fixture()
def request_warning(seed_data) -> CrearCitaRequest:
    return CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-21 15:00:00",
        fin="2024-05-21 15:20:00",
        motivo="Control con warning",
        estado=EstadoCita.PROGRAMADA.value,
    )


def _contar(tabla: str, container) -> int:
    return int(container.connection.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0])


def _ultima_auditoria(container) -> tuple[str, dict[str, object]]:
    row = container.connection.execute(
        "SELECT outcome, metadata_json FROM auditoria_eventos ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row is not None
    return row["outcome"], json.loads(row["metadata_json"] or "{}")


def test_crear_cita_autorizada_persiste_y_audita_ok(container, request_base) -> None:
    usecase = CrearCitaUseCase(container)

    resultado = usecase.execute(request_base)

    assert resultado.cita_id > 0
    assert resultado.incidencia_id is None
    cita = container.citas_repo.get_by_id(resultado.cita_id)
    assert cita is not None

    outcome, metadata = _ultima_auditoria(container)
    assert outcome == "ok"
    assert metadata == {
        "cita_id": resultado.cita_id,
        "medico_id": request_base.medico_id,
        "sala_id": request_base.sala_id,
        "warnings_count": 0,
        "incidencia_id": None,
    }


def test_crear_cita_sin_permiso_falla_antes_de_persistir_y_sin_efectos_parciales(container, request_base) -> None:
    container.user_context.role = Role.READONLY
    container.citas_repo = _RepoSpy(container.citas_repo)
    container.incidencias_repo = _RepoSpy(container.incidencias_repo)
    usecase = CrearCitaUseCase(container)
    citas_antes = _contar("citas", container)
    incidencias_antes = _contar("incidencias", container)

    with pytest.raises(AuthorizationError):
        usecase.execute(request_base)

    assert container.citas_repo.calls == 0
    assert container.incidencias_repo.calls == 0
    assert _contar("citas", container) == citas_antes
    assert _contar("incidencias", container) == incidencias_antes

    outcome, metadata = _ultima_auditoria(container)
    assert outcome == "fail"
    assert metadata == {
        "medico_id": request_base.medico_id,
        "sala_id": request_base.sala_id,
        "error_type": "AuthorizationError",
    }


def test_crear_cita_con_warning_exige_confirmacion_y_no_persiste_nada(container, request_warning) -> None:
    usecase = CrearCitaUseCase(container)
    citas_antes = _contar("citas", container)
    incidencias_antes = _contar("incidencias", container)

    with pytest.raises(PendingWarningsError):
        usecase.execute(request_warning)

    assert _contar("citas", container) == citas_antes
    assert _contar("incidencias", container) == incidencias_antes

    outcome, metadata = _ultima_auditoria(container)
    assert outcome == "fail"
    assert metadata == {
        "medico_id": request_warning.medico_id,
        "sala_id": request_warning.sala_id,
        "error_type": "PendingWarningsError",
    }


@pytest.mark.parametrize(
    ("nota_override", "confirmado_por_personal_id", "error"),
    [
        ("", 7, "nota_override"),
        ("Autorizado por coordinación", None, "confirmado_por_personal_id"),
    ],
)
def test_override_exige_nota_y_confirmador_sin_efectos_parciales(
    container,
    request_warning,
    nota_override: str,
    confirmado_por_personal_id: int | None,
    error: str,
    seed_data,
) -> None:
    usecase = CrearCitaUseCase(container)
    citas_antes = _contar("citas", container)
    incidencias_antes = _contar("incidencias", container)
    request_warning.override = True
    request_warning.nota_override = nota_override
    request_warning.confirmado_por_personal_id = confirmado_por_personal_id or seed_data["personal_activo_id"]
    if confirmado_por_personal_id is None:
        request_warning.confirmado_por_personal_id = None

    with pytest.raises(ValidationError, match=error):
        usecase.execute(request_warning)

    assert _contar("citas", container) == citas_antes
    assert _contar("incidencias", container) == incidencias_antes

    outcome, metadata = _ultima_auditoria(container)
    assert outcome == "fail"
    assert metadata == {
        "medico_id": request_warning.medico_id,
        "sala_id": request_warning.sala_id,
        "error_type": "ValidationError",
    }


def test_override_valido_crea_incidencia_y_audita_sin_pii_innecesaria(container, request_warning, seed_data) -> None:
    usecase = CrearCitaUseCase(container)
    request_warning.override = True
    request_warning.nota_override = "Paciente informado; coordinación valida la excepción"
    request_warning.confirmado_por_personal_id = seed_data["personal_activo_id"]

    resultado = usecase.execute(request_warning)

    assert resultado.cita_id > 0
    assert resultado.incidencia_id is not None
    incidencia = container.connection.execute(
        "SELECT cita_id, confirmado_por_personal_id, nota_override FROM incidencias WHERE id = ?",
        (resultado.incidencia_id,),
    ).fetchone()
    assert incidencia is not None
    assert incidencia["cita_id"] == resultado.cita_id
    assert incidencia["confirmado_por_personal_id"] == seed_data["personal_activo_id"]
    assert incidencia["nota_override"] == request_warning.nota_override

    outcome, metadata = _ultima_auditoria(container)
    assert outcome == "ok"
    assert metadata == {
        "cita_id": resultado.cita_id,
        "medico_id": request_warning.medico_id,
        "sala_id": request_warning.sala_id,
        "warnings_count": len(resultado.warnings),
        "incidencia_id": resultado.incidencia_id,
    }
    assert "paciente_id" not in metadata
    assert "motivo" not in metadata
    assert "nota_override" not in metadata
