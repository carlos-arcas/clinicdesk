from __future__ import annotations

from clinicdesk.app.queries.confirmaciones_queries import ConfirmacionesQueries, FiltrosConfirmacionesQuery


def _seed_base(db_connection):
    db_connection.execute(
        "INSERT INTO pacientes (id, tipo_documento, documento, nombre, apellidos, activo) VALUES (1,'DNI','1','Ana','Uno',1)"
    )
    db_connection.execute(
        "INSERT INTO pacientes (id, tipo_documento, documento, nombre, apellidos, activo) VALUES (2,'DNI','2','Beto','Dos',1)"
    )
    db_connection.execute(
        "INSERT INTO medicos (id, tipo_documento, documento, nombre, apellidos, num_colegiado, especialidad, activo) VALUES (1,'DNI','10','Marta','Med','COL1','General',1)"
    )
    db_connection.execute(
        "INSERT INTO salas (id, nombre, tipo, activa) VALUES (1,'S1','CONSULTA',1)"
    )


def test_buscar_confirmaciones_filtra_rango_estado_y_paginacion(db_connection):
    _seed_base(db_connection)
    db_connection.execute(
        "INSERT INTO citas (id,paciente_id,medico_id,sala_id,inicio,fin,estado,activo) VALUES (1,1,1,1,'2026-01-03T10:00:00','2026-01-03T10:30:00','PENDIENTE',1)"
    )
    db_connection.execute(
        "INSERT INTO citas (id,paciente_id,medico_id,sala_id,inicio,fin,estado,activo) VALUES (2,2,1,1,'2026-01-05T10:00:00','2026-01-05T10:30:00','PENDIENTE',1)"
    )
    db_connection.execute(
        "INSERT INTO citas (id,paciente_id,medico_id,sala_id,inicio,fin,estado,activo) VALUES (3,1,1,1,'2026-02-01T10:00:00','2026-02-01T10:30:00','PENDIENTE',1)"
    )
    db_connection.execute(
        "INSERT INTO citas (id,paciente_id,medico_id,sala_id,inicio,fin,estado,activo) VALUES (4,1,1,1,'2026-01-07T10:00:00','2026-01-07T10:30:00','PENDIENTE',1)"
    )
    db_connection.execute(
        "INSERT INTO recordatorios_citas (cita_id,canal,estado,created_at_utc,updated_at_utc) VALUES (1,'EMAIL','PREPARADO','2026-01-01T00:00:00','2026-01-01T00:00:00')"
    )
    db_connection.execute(
        "INSERT INTO recordatorios_citas (cita_id,canal,estado,created_at_utc,updated_at_utc) VALUES (1,'WHATSAPP','ENVIADO','2026-01-01T00:00:00','2026-01-01T00:00:00')"
    )
    db_connection.execute(
        "INSERT INTO recordatorios_citas (cita_id,canal,estado,created_at_utc,updated_at_utc) VALUES (2,'EMAIL','PREPARADO','2026-01-01T00:00:00','2026-01-01T00:00:00')"
    )
    db_connection.commit()

    q = ConfirmacionesQueries(db_connection)
    filtros = FiltrosConfirmacionesQuery(desde="2026-01-01", hasta="2026-01-31")
    items, total = q.buscar_citas_confirmaciones(filtros, limit=1, offset=0)

    assert total == 3
    assert len(items) == 1
    assert items[0].recordatorio_estado_global == "ENVIADO"

    items_2, _ = q.buscar_citas_confirmaciones(filtros, limit=10, offset=1)
    assert items_2[0].recordatorio_estado_global == "PREPARADO"

    sin_preparar, total_sin = q.buscar_citas_confirmaciones(
        FiltrosConfirmacionesQuery(
            desde="2026-01-01",
            hasta="2026-01-31",
            recordatorio_filtro="SIN_PREPARAR",
        ),
        limit=10,
        offset=0,
    )
    assert total_sin == 1
    assert sin_preparar[0].cita_id == 4
    assert sin_preparar[0].recordatorio_estado_global == "SIN_PREPARAR"
