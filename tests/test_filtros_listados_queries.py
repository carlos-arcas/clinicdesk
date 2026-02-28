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
