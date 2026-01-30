from __future__ import annotations

import pytest

from clinicdesk.app.application.usecases.crear_cita import CrearCitaRequest, CrearCitaUseCase
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
