from __future__ import annotations

import sqlite3

from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia
from clinicdesk.app.queries.incidencias_queries import IncidenciasQueries


def test_incidencias_create_list_filter(container, seed_data, assert_expected_actual) -> None:
    incidencias_repo = container.incidencias_repo

    incidencia = Incidencia(
        tipo="CITA",
        severidad="ALTA",
        estado="ABIERTA",
        fecha_hora="2024-05-20 11:00:00",
        descripcion="Cita creada con override",
        medico_id=seed_data["medico_activo_id"],
        personal_id=seed_data["personal_activo_id"],
        cita_id=None,
        dispensacion_id=None,
        receta_id=None,
        confirmado_por_personal_id=seed_data["personal_activo_id"],
        nota_override="Aprobado por urgencia",
    )

    incidencia_id = incidencias_repo.create(incidencia)
    stored = incidencias_repo.get_by_id(incidencia_id)
    assert stored is not None

    assert_expected_actual(
        {
            "tipo": "CITA",
            "severidad": "ALTA",
            "estado": "ABIERTA",
        },
        {
            "tipo": stored.tipo,
            "severidad": stored.severidad,
            "estado": stored.estado,
        },
        message="Incidencia creada: esperado vs obtenido",
    )

    queries = IncidenciasQueries(container.connection)
    resultados = queries.list(tipo="CITA", severidad="ALTA")
    assert resultados, "Debe listar incidencias filtradas por tipo/severidad"

    assert_expected_actual(
        {
            "tipo": "CITA",
            "severidad": "ALTA",
            "confirmado_por": "Carla",
        },
        {
            "tipo": resultados[0].tipo,
            "severidad": resultados[0].severidad,
            "confirmado_por": resultados[0].confirmado_por_nombre.split(" ")[0],
        },
        message="Listado de incidencias filtrado: esperado vs obtenido",
    )

    texto = queries.list(texto="override")
    assert texto, "Filtro por texto debe encontrar incidencia creada"


def _conexion_incidencias_nullable() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE personal (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL
        );

        CREATE TABLE medicos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL
        );

        CREATE TABLE incidencias (
            id INTEGER PRIMARY KEY,
            tipo TEXT NOT NULL,
            severidad TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_hora TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            nota_override TEXT NOT NULL,
            confirmado_por_personal_id INTEGER,
            medico_id INTEGER,
            personal_id INTEGER,
            cita_id INTEGER,
            receta_id INTEGER,
            dispensacion_id INTEGER,
            activo INTEGER NOT NULL DEFAULT 1
        );
        """
    )
    con.execute("INSERT INTO personal (id, nombre, apellidos) VALUES (1, 'Carla', 'Ruiz')")
    con.execute("INSERT INTO personal (id, nombre, apellidos) VALUES (2, 'Nora', 'Paz')")
    con.execute("INSERT INTO medicos (id, nombre, apellidos) VALUES (1, 'Mario', 'Sanz')")
    con.executemany(
        """
        INSERT INTO incidencias (
            id, tipo, severidad, estado, fecha_hora, descripcion, nota_override,
            confirmado_por_personal_id, medico_id, personal_id, cita_id, receta_id, dispensacion_id, activo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        [
            (
                1,
                "CITA",
                "ALTA",
                "ABIERTA",
                "2025-03-01 09:30:00",
                "Incidencia confirmada",
                "Validada",
                1,
                1,
                2,
                100,
                None,
                None,
            ),
            (
                2,
                "CITA",
                "MEDIA",
                "ABIERTA",
                "2025-03-02 10:00:00",
                "Incidencia sin confirmar",
                "Pendiente",
                None,
                None,
                2,
                101,
                None,
                None,
            ),
        ],
    )
    con.commit()
    return con


def test_incidencias_queries_mapea_confirmador_nullable() -> None:
    queries = IncidenciasQueries(_conexion_incidencias_nullable())

    resultados = queries.list(tipo="CITA")

    assert [row.id for row in resultados] == [2, 1]
    sin_confirmar, confirmada = resultados
    assert sin_confirmar.confirmado_por_personal_id is None
    assert sin_confirmar.confirmado_por_nombre is None
    assert confirmada.confirmado_por_personal_id == 1
    assert confirmada.confirmado_por_nombre == "Carla Ruiz"


def test_incidencias_queries_get_by_id_no_pierde_incidencia_sin_confirmador() -> None:
    queries = IncidenciasQueries(_conexion_incidencias_nullable())

    row = queries.get_by_id(2)

    assert row is not None
    assert row.id == 2
    assert row.confirmado_por_personal_id is None
    assert row.confirmado_por_nombre is None


def test_incidencias_queries_soporta_confirmador_huerfano_sin_filtrar_fila() -> None:
    con = _conexion_incidencias_nullable()
    con.execute(
        """
        INSERT INTO incidencias (
            id, tipo, severidad, estado, fecha_hora, descripcion, nota_override,
            confirmado_por_personal_id, medico_id, personal_id, cita_id, receta_id, dispensacion_id, activo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            3,
            "CITA",
            "BAJA",
            "ABIERTA",
            "2025-03-03 10:00:00",
            "Incidencia con confirmador legado",
            "Migrada",
            999,
            None,
            None,
            102,
            None,
            None,
        ),
    )
    con.commit()
    queries = IncidenciasQueries(con)

    row = queries.get_by_id(3)

    assert row is not None
    assert row.confirmado_por_personal_id == 999
    assert row.confirmado_por_nombre is None
