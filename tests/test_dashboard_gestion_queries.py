from __future__ import annotations

from datetime import date

from clinicdesk.app.queries.dashboard_gestion_queries import DashboardGestionQueries


def test_listar_salas_filtro_usa_columna_activa_schema_real(db_connection) -> None:
    db_connection.execute("INSERT INTO salas(nombre, tipo, ubicacion, activa) VALUES ('Sala A', 'CONSULTA', 'P1', 1)")
    db_connection.execute("INSERT INTO salas(nombre, tipo, ubicacion, activa) VALUES ('Sala B', 'CONSULTA', 'P1', 0)")
    db_connection.commit()

    rows = DashboardGestionQueries(db_connection).listar_salas_filtro()

    assert [row.etiqueta for row in rows] == ["Sala A"]


def test_obtener_resumen_centro_salud_usa_predicciones_log_y_no_columna_inexistente(db_connection) -> None:
    db_connection.execute(
        "INSERT INTO pacientes(tipo_documento, documento, nombre, apellidos, activo) VALUES ('DNI','1','Ana','Uno',1)"
    )
    db_connection.execute("INSERT INTO medicos(tipo_documento, documento, nombre, apellidos, num_colegiado, especialidad, activo) VALUES ('DNI','2','Doc','Uno','COL-1','MED',1)")
    db_connection.execute("INSERT INTO salas(nombre, tipo, ubicacion, activa) VALUES ('Sala 1','CONSULTA','P1',1)")
    db_connection.execute(
        """
        INSERT INTO citas(paciente_id, medico_id, sala_id, inicio, fin, estado, activo)
        VALUES (1, 1, 1, '2026-01-10 10:00:00', '2026-01-10 10:30:00', 'PROGRAMADA', 1)
        """
    )
    db_connection.execute(
        """
        INSERT INTO predicciones_ausencias_log(timestamp_utc, modelo_fecha_utc, cita_id, riesgo, source)
        VALUES
          ('2026-01-09T00:00:00Z', '2026-01-09T00:00:00Z', 1, 'MEDIO', 'test'),
          ('2026-01-10T00:00:00Z', '2026-01-10T00:00:00Z', 1, 'ALTO', 'test')
        """
    )
    db_connection.commit()

    resumen = DashboardGestionQueries(db_connection).obtener_resumen_centro_salud(
        desde=date(2026, 1, 1),
        hasta=date(2026, 1, 31),
        medico_id=None,
        sala_id=None,
        estado=None,
    )

    assert resumen.total_citas == 1
    assert resumen.total_riesgo_alto == 1
    assert resumen.riesgo_medio_pct == 100.0
