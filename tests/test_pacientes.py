from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.queries.pacientes_queries import PacientesQueries


def test_pacientes_crud_and_search(container, seed_data, assert_expected_actual) -> None:
    pacientes_repo = container.pacientes_repo

    paciente = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="55544433",
        nombre="Ana",
        apellidos="Suarez",
        telefono="644555666",
        email="ana@example.test",
        fecha_nacimiento=date(1992, 7, 10),
        direccion="Calle Norte 9",
        activo=True,
        num_historia="H-200",
        alergias="Penicilina",
        observaciones=None,
    )

    paciente_id = pacientes_repo.create(paciente)
    stored = pacientes_repo.get_by_id(paciente_id)
    assert stored is not None

    assert_expected_actual(
        {
            "documento": "55544433",
            "nombre": "Ana",
            "apellidos": "Suarez",
            "telefono": "644555666",
            "email": "ana@example.test",
            "activo": True,
            "num_historia": "H-200",
        },
        {
            "documento": stored.documento,
            "nombre": stored.nombre,
            "apellidos": stored.apellidos,
            "telefono": stored.telefono,
            "email": stored.email,
            "activo": stored.activo,
            "num_historia": stored.num_historia,
        },
        message="Paciente creado: esperado vs obtenido",
    )

    stored.nombre = "Ana Maria"
    stored.telefono = "699888777"
    pacientes_repo.update(stored)

    updated = pacientes_repo.get_by_id(paciente_id)
    assert updated is not None
    assert_expected_actual(
        {
            "nombre": "Ana Maria",
            "telefono": "699888777",
        },
        {
            "nombre": updated.nombre,
            "telefono": updated.telefono,
        },
        message="Paciente actualizado: esperado vs obtenido",
    )

    pacientes_repo.delete(paciente_id)
    activos = pacientes_repo.list_all(solo_activos=True)
    assert all(p.id != paciente_id for p in activos), "Paciente desactivado no debe estar activo"

    queries = PacientesQueries(container.connection)
    resultados = queries.search(texto="600 123")
    documentos = [r.documento for r in resultados]
    assert "12345678" in documentos, "Búsqueda por teléfono parcial debe incluir paciente activo"

    inactivos = pacientes_repo.search(activo=False)
    inactivos_ids = [p.id for p in inactivos]
    assert seed_data["paciente_inactivo_id"] in inactivos_ids, "Paciente inactivo debe aparecer en filtro activo=False"


def test_pacientes_documento_duplicado(container) -> None:
    pacientes_repo = container.pacientes_repo

    paciente = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="11122233",
        nombre="Luis",
        apellidos="Sanchez",
        telefono="611222333",
        email=None,
        fecha_nacimiento=None,
        direccion=None,
        activo=True,
        num_historia=None,
        alergias=None,
        observaciones=None,
    )

    pacientes_repo.create(paciente)

    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        pacientes_repo.create(paciente)
