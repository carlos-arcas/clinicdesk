from __future__ import annotations

from datetime import datetime

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Medico, Medicamento, Paciente
from clinicdesk.app.domain.modelos import Receta, RecetaLinea
from clinicdesk.app.queries.recetas_queries import RecetasQueries


def _seed_base(container):
    paciente_id = container.pacientes_repo.create(
        Paciente(
            tipo_documento=TipoDocumento.DNI,
            documento="10000000",
            nombre="Nora",
            apellidos="Paz",
            telefono="611111111",
            email=None,
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            num_historia=None,
            alergias=None,
            observaciones=None,
        )
    )
    medico_id = container.medicos_repo.create(
        Medico(
            tipo_documento=TipoDocumento.DNI,
            documento="20000000",
            nombre="Mario",
            apellidos="Linares",
            telefono=None,
            email=None,
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            num_colegiado="COL-777",
            especialidad="General",
        )
    )
    medicamento_id = container.medicamentos_repo.create(
        Medicamento(
            nombre_compuesto="Paracetamol",
            nombre_comercial="Gelocatil",
            cantidad_almacen=100,
            activo=True,
        )
    )
    return paciente_id, medico_id, medicamento_id


def test_list_flat_por_paciente_filtra_y_ordena_por_fecha_desc(container) -> None:
    paciente_id, medico_id, medicamento_id = _seed_base(container)
    otro_paciente_id = container.pacientes_repo.create(
        Paciente(
            tipo_documento=TipoDocumento.DNI,
            documento="30000000",
            nombre="Otro",
            apellidos="Paciente",
            telefono=None,
            email=None,
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            num_historia=None,
            alergias=None,
            observaciones=None,
        )
    )
    receta_antigua = container.recetas_repo.create_receta(
        Receta(paciente_id=paciente_id, medico_id=medico_id, fecha=datetime(2024, 1, 10, 8, 0, 0))
    )
    receta_nueva = container.recetas_repo.create_receta(
        Receta(paciente_id=paciente_id, medico_id=medico_id, fecha=datetime(2024, 2, 10, 8, 0, 0))
    )
    container.recetas_repo.create_receta(
        Receta(paciente_id=otro_paciente_id, medico_id=medico_id, fecha=datetime(2024, 3, 10, 8, 0, 0))
    )
    container.recetas_repo.add_linea(
        RecetaLinea(receta_id=receta_antigua, medicamento_id=medicamento_id, dosis="1/8h", duracion_dias=5)
    )

    rows = RecetasQueries(container.connection).list_flat_por_paciente(paciente_id)

    assert [row.receta_id for row in rows] == [receta_nueva, receta_antigua]


def test_list_flat_por_paciente_asocia_lineas_por_receta(container) -> None:
    paciente_id, medico_id, medicamento_id = _seed_base(container)
    receta_id = container.recetas_repo.create_receta(
        Receta(paciente_id=paciente_id, medico_id=medico_id, fecha=datetime(2024, 2, 1, 9, 0, 0))
    )
    container.recetas_repo.add_linea(
        RecetaLinea(receta_id=receta_id, medicamento_id=medicamento_id, dosis="1/12h", duracion_dias=3)
    )
    container.recetas_repo.add_linea(
        RecetaLinea(receta_id=receta_id, medicamento_id=medicamento_id, dosis="1/24h", duracion_dias=7)
    )

    rows = RecetasQueries(container.connection).list_flat_por_paciente(paciente_id)

    assert len(rows) == 2
    assert {row.linea_dosis for row in rows} == {"1/12h", "1/24h"}
    assert all(row.receta_id == receta_id for row in rows)
