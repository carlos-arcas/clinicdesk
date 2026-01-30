from __future__ import annotations

from clinicdesk.app.infrastructure.sqlite.repos_dispensaciones import Dispensacion
from clinicdesk.app.queries.dispensaciones_queries import DispensacionesQueries


def test_dispensaciones_create_and_filter(container, seed_data, assert_expected_actual) -> None:
    pacientes_repo = container.pacientes_repo
    personal_repo = container.personal_repo
    medicamentos_repo = container.medicamentos_repo
    dispensaciones_repo = container.dispensaciones_repo

    paciente_id = pacientes_repo.get_id_by_documento("DNI", "12345678")
    personal_id = personal_repo.get_id_by_documento("DNI", "11223344")
    medicamento_id = medicamentos_repo.get_id_by_nombre("Amoxil")

    assert paciente_id is not None, "Debe resolver paciente por documento"
    assert personal_id is not None, "Debe resolver personal por documento"
    assert medicamento_id is not None, "Debe resolver medicamento por nombre"

    dispensacion = Dispensacion(
        receta_id=seed_data["receta_id"],
        receta_linea_id=seed_data["receta_linea_id"],
        medicamento_id=medicamento_id,
        personal_id=personal_id,
        cantidad=1,
        fecha_hora="2024-05-20 10:05:00",
        incidencia=False,
        notas_incidencia=None,
    )

    dispensacion_id = dispensaciones_repo.create(dispensacion)
    stored = dispensaciones_repo.get_by_id(dispensacion_id)
    assert stored is not None

    assert_expected_actual(
        {
            "receta_id": seed_data["receta_id"],
            "medicamento_id": medicamento_id,
            "personal_id": personal_id,
            "cantidad": 1,
        },
        {
            "receta_id": stored.receta_id,
            "medicamento_id": stored.medicamento_id,
            "personal_id": stored.personal_id,
            "cantidad": stored.cantidad,
        },
        message="Dispensación creada: esperado vs obtenido",
    )

    queries = DispensacionesQueries(container.connection)
    rows = queries.list(paciente_texto="Laura", medicamento_texto="Amox")
    assert rows, "Dispensación debe aparecer en filtros por paciente/medicamento"

    assert_expected_actual(
        {
            "paciente": "Laura",
            "medicamento": "Amoxil",
            "cantidad": 1,
        },
        {
            "paciente": rows[0].paciente.split(" ")[0],
            "medicamento": rows[0].medicamento,
            "cantidad": rows[0].cantidad,
        },
        message="Filtro de dispensaciones: esperado vs obtenido",
    )
