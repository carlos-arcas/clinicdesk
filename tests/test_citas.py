from __future__ import annotations

from datetime import datetime

import pytest

from clinicdesk.app.application.usecases.crear_cita import (
    CrearCitaRequest,
    CrearCitaUseCase,
    PendingWarningsError,
)
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.queries.citas_queries import CitasQueries


def test_citas_create_list_delete(container, seed_data, assert_expected_actual) -> None:
    usecase = CrearCitaUseCase(container)

    request = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-20 09:00:00",
        fin="2024-05-20 09:30:00",
        motivo="Consulta general",
        observaciones=None,
        estado=EstadoCita.PROGRAMADA.value,
    )

    result = usecase.execute(request)

    assert_expected_actual(
        {"warnings": 0},
        {"warnings": len(result.warnings)},
        message="Crear cita sin warnings debe devolver 0 warnings",
    )

    queries = CitasQueries(container)
    rows = queries.list_by_date("2024-05-20")

    assert rows, "Debe listar la cita creada por fecha"
    assert_expected_actual(
        {
            "paciente_id": seed_data["paciente_activo_id"],
            "medico_id": seed_data["medico_activo_id"],
            "sala_id": seed_data["sala_activa_id"],
            "estado": EstadoCita.PROGRAMADA.value,
        },
        {
            "paciente_id": rows[0].paciente_id,
            "medico_id": rows[0].medico_id,
            "sala_id": rows[0].sala_id,
            "estado": rows[0].estado,
        },
        message="Listado de citas por fecha: esperado vs obtenido",
    )

    citas_repo = CitasRepository(container.connection)
    citas_repo.delete(result.cita_id)

    rows_after = queries.list_by_date("2024-05-20")
    assert rows_after == [], "Cita eliminada no debe aparecer en listado"


def test_citas_solape_validation(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)

    base_request = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-20 10:00:00",
        fin="2024-05-20 10:30:00",
        motivo="Control",
        observaciones=None,
        estado=EstadoCita.PROGRAMADA.value,
    )

    usecase.execute(base_request)

    overlap_request = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-20 10:15:00",
        fin="2024-05-20 10:45:00",
        motivo="Solape",
        observaciones=None,
        estado=EstadoCita.PROGRAMADA.value,
    )

    with pytest.raises(ValidationError, match="solape"):
        usecase.execute(overlap_request)


def test_citas_warning_requires_override(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)

    req = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-21 09:00:00",
        fin="2024-05-21 09:30:00",
        motivo="Sin cuadrante",
        estado=EstadoCita.PROGRAMADA.value,
    )

    with pytest.raises(PendingWarningsError):
        usecase.execute(req)


def test_citas_override_crea_incidencia_y_actualiza_estado(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)

    req = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-21 11:00:00",
        fin="2024-05-21 11:30:00",
        motivo="Con override",
        estado=EstadoCita.PROGRAMADA.value,
        override=True,
        nota_override="Autorizado por coordinación",
        confirmado_por_personal_id=seed_data["personal_activo_id"],
    )

    result = usecase.execute(req)
    assert result.incidencia_id is not None

    citas_repo = CitasRepository(container.connection)
    cita = citas_repo.get_by_id(result.cita_id)
    assert cita is not None
    cita.estado = EstadoCita.REALIZADA
    citas_repo.update(cita)

    by_medico = citas_repo.list_by_medico(seed_data["medico_activo_id"])
    by_paciente = citas_repo.list_by_paciente(seed_data["paciente_activo_id"])
    by_sala = citas_repo.list_by_sala(seed_data["sala_activa_id"])
    realizadas = citas_repo.list_by_estado(EstadoCita.REALIZADA.value)

    assert any(item.id == result.cita_id for item in by_medico)
    assert any(item.id == result.cita_id for item in by_paciente)
    assert any(item.id == result.cita_id for item in by_sala)
    assert any(item.id == result.cita_id for item in realizadas)


def test_citas_list_in_range_returns_only_requested_window(container, seed_data) -> None:
    usecase = CrearCitaUseCase(container)
    req_in = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-20 12:00:00",
        fin="2024-05-20 12:20:00",
        motivo="En rango",
        estado=EstadoCita.PROGRAMADA.value,
    )
    req_out = CrearCitaRequest(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2024-05-21 12:00:00",
        fin="2024-05-21 12:20:00",
        motivo="Fuera de rango",
        estado=EstadoCita.PROGRAMADA.value,
        override=True,
        nota_override="Autorizado por coordinación",
        confirmado_por_personal_id=seed_data["personal_activo_id"],
    )
    usecase.execute(req_in)
    usecase.execute(req_out)

    citas_repo = CitasRepository(container.connection)
    rows = citas_repo.list_in_range(
        desde=datetime(2024, 5, 20, 0, 0, 0),
        hasta=datetime(2024, 5, 20, 23, 59, 59),
    )

    assert len(rows) == 1
    assert rows[0].motivo == "En rango"


def test_citas_list_in_range_validates_temporal_window(container) -> None:
    citas_repo = CitasRepository(container.connection)

    with pytest.raises(ValidationError, match="Rango inválido"):
        citas_repo.list_in_range(
            desde=datetime(2024, 5, 22, 0, 0, 0),
            hasta=datetime(2024, 5, 20, 23, 59, 59),
        )
