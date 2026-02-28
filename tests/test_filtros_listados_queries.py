from __future__ import annotations

import sqlite3

from clinicdesk.app.queries.materiales_queries import MaterialesQueries
from clinicdesk.app.queries.medicos_queries import MedicosQueries
from clinicdesk.app.queries.medicamentos_queries import MedicamentosQueries
from clinicdesk.app.queries.pacientes_queries import PacientesQueries
from clinicdesk.app.queries.personal_queries import PersonalQueries
from clinicdesk.app.queries.salas_queries import SalasQueries


def test_filtros_texto_y_estado_en_queries(container, seed_data) -> None:
    pacientes = PacientesQueries(container.connection)
    assert all(item.activo for item in pacientes.search(texto="Laura", activo=True))

    personal = PersonalQueries(container.connection)
    assert all(not item.activo for item in personal.search(texto="Raul", activo=False))

    salas = SalasQueries(container.connection)
    assert all(item.activa for item in salas.search(texto="Consulta", activa=True))

    medicamentos = MedicamentosQueries(container.connection)
    assert all(item.activo for item in medicamentos.search(texto="Amox", activo=True))

    materiales = MaterialesQueries(container.connection)
    assert all(item.activo for item in materiales.search(texto="Guantes", activo=True))


def test_medicos_queries_agrupa_especialidades_sin_duplicar() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE medicos (
            id INTEGER,
            documento TEXT,
            nombre TEXT,
            apellidos TEXT,
            telefono TEXT,
            num_colegiado TEXT,
            especialidad TEXT,
            activo INTEGER
        );

        INSERT INTO medicos(id, documento, nombre, apellidos, telefono, num_colegiado, especialidad, activo)
        VALUES
            (1, '123', 'Ana', 'Lopez', '600111222', 'MED-1', 'Cardiología', 1),
            (1, '123', 'Ana', 'Lopez', '600111222', 'MED-1', 'Pediatría', 1),
            (2, '456', 'Luis', 'Perez', '600222333', 'MED-2', 'Traumatología', 1);
        """
    )

    queries = MedicosQueries(conn)
    rows = queries.list_all(activo=True)

    assert len(rows) == 2
    assert rows[0].id == 1
    assert rows[0].especialidad == "Cardiología,Pediatría"


def test_medicos_queries_aplica_paginacion_y_orden_estable_por_id() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE medicos (
            id INTEGER,
            documento TEXT,
            nombre TEXT,
            apellidos TEXT,
            telefono TEXT,
            num_colegiado TEXT,
            especialidad TEXT,
            activo INTEGER
        );

        INSERT INTO medicos(id, documento, nombre, apellidos, telefono, num_colegiado, especialidad, activo)
        VALUES
            (3, 'D3', 'Ariadna', 'Ruiz', '600333333', 'MED-3', 'Cardiología', 1),
            (1, 'D1', 'Ariadna', 'Ruiz', '600111111', 'MED-1', 'Cardiología', 1),
            (2, 'D2', 'Ariadna', 'Ruiz', '600222222', 'MED-2', 'Cardiología', 1);
        """
    )

    queries = MedicosQueries(conn)

    first_page = queries.list_all(activo=True, limit=2, offset=0)
    second_page = queries.list_all(activo=True, limit=2, offset=2)

    assert [row.id for row in first_page] == [1, 2]
    assert [row.id for row in second_page] == [3]


def test_pacientes_queries_aplica_paginacion_y_orden_estable_por_id() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE pacientes (
            id INTEGER,
            tipo_documento TEXT,
            documento TEXT,
            nombre TEXT,
            apellidos TEXT,
            telefono TEXT,
            fecha_nacimiento TEXT,
            activo INTEGER
        );

        INSERT INTO pacientes(id, tipo_documento, documento, nombre, apellidos, telefono, fecha_nacimiento, activo)
        VALUES
            (3, 'DNI', 'P3', 'Claudia', 'Soto', '600333333', '1990-01-01', 1),
            (1, 'DNI', 'P1', 'Claudia', 'Soto', '600111111', '1990-01-01', 1),
            (2, 'DNI', 'P2', 'Claudia', 'Soto', '600222222', '1990-01-01', 1);
        """
    )

    queries = PacientesQueries(conn)

    first_page = queries.list_all(activo=True, limit=2, offset=0)
    second_page = queries.list_all(activo=True, limit=2, offset=2)

    assert [row.id for row in first_page] == [1, 2]
    assert [row.id for row in second_page] == [3]
