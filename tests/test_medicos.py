from __future__ import annotations

from datetime import date

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Medico
from clinicdesk.app.queries.medicos_queries import MedicosQueries


def test_medicos_crud_and_search(container, seed_data, assert_expected_actual) -> None:
    medicos_repo = container.medicos_repo

    medico = Medico(
        tipo_documento=TipoDocumento.DNI,
        documento="33445566",
        nombre="Ines",
        apellidos="Ramos",
        telefono="677888999",
        email="ines@clinic.test",
        fecha_nacimiento=date(1980, 1, 5),
        direccion="Avenida Central 10",
        activo=True,
        num_colegiado="MED-300",
        especialidad="Dermatologia",
    )

    medico_id = medicos_repo.create(medico)
    stored = medicos_repo.get_by_id(medico_id)
    assert stored is not None

    assert_expected_actual(
        {
            "documento": "33445566",
            "nombre": "Ines",
            "especialidad": "Dermatologia",
            "activo": True,
        },
        {
            "documento": stored.documento,
            "nombre": stored.nombre,
            "especialidad": stored.especialidad,
            "activo": stored.activo,
        },
        message="Médico creado: esperado vs obtenido",
    )

    stored.especialidad = "Medicina interna"
    stored.telefono = "600111222"
    medicos_repo.update(stored)

    updated = medicos_repo.get_by_id(medico_id)
    assert updated is not None

    assert_expected_actual(
        {
            "especialidad": "Medicina interna",
            "telefono": "600111222",
        },
        {
            "especialidad": updated.especialidad,
            "telefono": updated.telefono,
        },
        message="Médico actualizado: esperado vs obtenido",
    )

    medicos_repo.delete(medico_id)
    activos = medicos_repo.list_all(solo_activos=True)
    assert all(m.id != medico_id for m in activos), "Médico desactivado no debe estar en activos"

    queries = MedicosQueries(container.connection)
    resultados = queries.search(texto="Elena", especialidad=None)
    nombres = [r.nombre_completo for r in resultados]
    assert any("Elena" in nombre for nombre in nombres), "Búsqueda parcial por nombre debería encontrar médico"

    filtro_especialidad = queries.search(especialidad="Pediatria")
    especialidades = {r.especialidad for r in filtro_especialidad}
    assert "Pediatria" in especialidades, "Filtro por especialidad debe incluir médicos de esa especialidad"

    inactivos = medicos_repo.search(activo=False)
    inactivos_ids = [m.id for m in inactivos]
    assert seed_data["medico_inactivo_id"] in inactivos_ids, "Médico inactivo debe aparecer con activo=False"


def test_medicos_queries_support_offset_limit_and_stable_order(container) -> None:
    queries = MedicosQueries(container.connection)
    repo = container.medicos_repo

    created_ids = []
    for idx in range(3):
        medico = Medico(
            tipo_documento=TipoDocumento.DNI,
            documento=f"9988776{idx}",
            nombre="Orden",
            apellidos="Estable",
            telefono=f"6000000{idx}",
            email=None,
            fecha_nacimiento=date(1985, 1, idx + 1),
            direccion=None,
            activo=True,
            num_colegiado=f"EST-{idx}",
            especialidad="General",
        )
        created_ids.append(repo.create(medico))

    ordered_rows = [
        row for row in queries.search(texto="Orden", activo=True, limit=None) if row.documento.startswith("9988776")
    ]
    assert [row.id for row in ordered_rows] == sorted(created_ids)

    first_page = queries.search(texto="Orden", activo=True, limit=2, offset=0)
    second_page = queries.search(texto="Orden", activo=True, limit=2, offset=2)

    paged_ids = [row.id for row in first_page + second_page if row.documento.startswith("9988776")]
    assert paged_ids[:3] == sorted(created_ids)
