from __future__ import annotations

from datetime import date

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.queries.personal_queries import PersonalQueries


def test_personal_crud_and_search(container, seed_data, assert_expected_actual) -> None:
    personal_repo = container.personal_repo

    personal = Personal(
        tipo_documento=TipoDocumento.DNI,
        documento="22113344",
        nombre="Sofia",
        apellidos="Navarro",
        telefono="655444333",
        email=None,
        fecha_nacimiento=date(1995, 2, 15),
        direccion=None,
        activo=True,
        puesto="Recepcion",
        turno=None,
    )

    personal_id = personal_repo.create(personal)
    stored = personal_repo.get_by_id(personal_id)
    assert stored is not None

    assert_expected_actual(
        {
            "documento": "22113344",
            "nombre": "Sofia",
            "puesto": "Recepcion",
            "activo": True,
        },
        {
            "documento": stored.documento,
            "nombre": stored.nombre,
            "puesto": stored.puesto,
            "activo": stored.activo,
        },
        message="Personal creado: esperado vs obtenido",
    )

    stored.puesto = "Administracion"
    stored.telefono = "655000111"
    personal_repo.update(stored)

    updated = personal_repo.get_by_id(personal_id)
    assert updated is not None

    assert_expected_actual(
        {
            "puesto": "Administracion",
            "telefono": "655000111",
        },
        {
            "puesto": updated.puesto,
            "telefono": updated.telefono,
        },
        message="Personal actualizado: esperado vs obtenido",
    )

    personal_repo.delete(personal_id)
    activos = personal_repo.list_all(solo_activos=True)
    assert all(p.id != personal_id for p in activos), "Personal desactivado no debe estar activo"

    queries = PersonalQueries(container.connection)
    resultados = queries.search(texto="Enfer")
    puestos = [r.puesto for r in resultados]
    assert "Enfermeria" in puestos, "Búsqueda parcial debe encontrar puesto"

    filtro_puesto = queries.search(puesto="Enfermeria")
    assert all(r.puesto == "Enfermeria" for r in filtro_puesto), "Filtro por puesto debe respetarse"

    inactivos = personal_repo.search(activo=False)
    inactivos_ids = [p.id for p in inactivos]
    assert seed_data["personal_inactivo_id"] in inactivos_ids, "Personal inactivo debe aparecer en activo=False"
