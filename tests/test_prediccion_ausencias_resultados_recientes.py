from __future__ import annotations

from datetime import datetime, timedelta, timezone

from clinicdesk.app.application.prediccion_ausencias.resultados_recientes import (
    ObtenerResultadosRecientesPrediccionAusencias,
)
from clinicdesk.app.queries.prediccion_ausencias_resultados_queries import (
    ItemRegistroPrediccionAusencia,
    PrediccionAusenciasResultadosQueries,
)


def _seed_base_tablas(con) -> tuple[int, int, int]:
    con.execute(
        "INSERT INTO pacientes(tipo_documento, documento, nombre, apellidos, activo) VALUES ('DNI', '1', 'Ana', 'Uno', 1)"
    )
    con.execute(
        "INSERT INTO medicos(tipo_documento, documento, nombre, apellidos, activo, num_colegiado, especialidad) VALUES ('DNI', '11', 'Med', 'Uno', 1, 'C1', 'General')"
    )
    con.execute("INSERT INTO salas(nombre, tipo, activa) VALUES ('S1', 'CONSULTA', 1)")
    con.commit()
    return 1, 1, 1


def _insert_cita(con, *, cita_id: int, paciente_id: int, medico_id: int, sala_id: int, dias: int, estado: str) -> None:
    inicio = datetime.now(timezone.utc) - timedelta(days=dias)
    fin = inicio + timedelta(minutes=30)
    con.execute(
        """
        INSERT INTO citas(id, paciente_id, medico_id, sala_id, inicio, fin, estado, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (cita_id, paciente_id, medico_id, sala_id, inicio.isoformat(), fin.isoformat(), estado),
    )


def test_registro_predicciones_es_idempotente(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    _insert_cita(db_connection, cita_id=1, paciente_id=paciente_id, medico_id=medico_id, sala_id=sala_id, dias=2, estado="REALIZADA")
    db_connection.commit()

    queries = PrediccionAusenciasResultadosQueries(db_connection)
    item = ItemRegistroPrediccionAusencia(
        cita_id=1,
        riesgo="ALTO",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        source="agenda",
    )

    primera = queries.registrar_predicciones_ausencias("vA", [item])
    segunda = queries.registrar_predicciones_ausencias("vA", [item])
    total = db_connection.execute("SELECT COUNT(1) AS total FROM predicciones_ausencias_log").fetchone()["total"]

    assert primera == 1
    assert segunda == 0
    assert int(total) == 1


def test_obtener_resultados_recientes_agrega_por_riesgo(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    _insert_cita(db_connection, cita_id=1, paciente_id=paciente_id, medico_id=medico_id, sala_id=sala_id, dias=3, estado="NO_PRESENTADO")
    _insert_cita(db_connection, cita_id=2, paciente_id=paciente_id, medico_id=medico_id, sala_id=sala_id, dias=5, estado="REALIZADA")
    _insert_cita(db_connection, cita_id=3, paciente_id=paciente_id, medico_id=medico_id, sala_id=sala_id, dias=6, estado="NO_PRESENTADO")
    _insert_cita(db_connection, cita_id=4, paciente_id=paciente_id, medico_id=medico_id, sala_id=sala_id, dias=7, estado="REALIZADA")
    db_connection.commit()

    queries = PrediccionAusenciasResultadosQueries(db_connection)
    timestamp = datetime.now(timezone.utc).isoformat()
    version = "2026-01-01T00:00:00+00:00"
    queries.registrar_predicciones_ausencias(
        version,
        [
            ItemRegistroPrediccionAusencia(cita_id=1, riesgo="ALTO", timestamp_utc=timestamp, source="agenda"),
            ItemRegistroPrediccionAusencia(cita_id=2, riesgo="ALTO", timestamp_utc=timestamp, source="agenda"),
            ItemRegistroPrediccionAusencia(cita_id=3, riesgo="MEDIO", timestamp_utc=timestamp, source="agenda"),
            ItemRegistroPrediccionAusencia(cita_id=4, riesgo="BAJO", timestamp_utc=timestamp, source="agenda"),
            ItemRegistroPrediccionAusencia(cita_id=4, riesgo="NO_DISPONIBLE", timestamp_utc=timestamp, source="agenda"),
        ],
    )

    resultado = queries.obtener_resultados_recientes_prediccion(ventana_dias=60)
    filas = {fila.riesgo: fila for fila in resultado.filas}

    assert resultado.version_modelo_fecha_utc == version
    assert filas["ALTO"].total_predichas == 2
    assert filas["ALTO"].total_no_vino == 1
    assert filas["ALTO"].total_vino == 1
    assert filas["MEDIO"].total_predichas == 1
    assert filas["MEDIO"].total_no_vino == 1
    assert filas["BAJO"].total_predichas == 1
    assert filas["BAJO"].total_vino == 1


def test_uc_resultados_recientes_evalua_umbral(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    for cita_id in range(1, 22):
        estado = "NO_PRESENTADO" if cita_id % 3 == 0 else "REALIZADA"
        _insert_cita(
            db_connection,
            cita_id=cita_id,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            dias=10,
            estado=estado,
        )
    db_connection.commit()

    queries = PrediccionAusenciasResultadosQueries(db_connection)
    timestamp = datetime.now(timezone.utc).isoformat()

    queries.registrar_predicciones_ausencias(
        "v1",
        [
            ItemRegistroPrediccionAusencia(cita_id=1, riesgo="ALTO", timestamp_utc=timestamp, source="agenda"),
            ItemRegistroPrediccionAusencia(cita_id=2, riesgo="MEDIO", timestamp_utc=timestamp, source="agenda"),
        ],
    )
    uc = ObtenerResultadosRecientesPrediccionAusencias(queries, umbral_minimo=20)
    sin_datos = uc.ejecutar(ventana_dias=60)

    assert sin_datos.estado_evaluacion == "SIN_DATOS"
    assert sin_datos.mensaje_i18n_key == "prediccion_ausencias.resultados.estado.sin_datos"

    many_items = [
        ItemRegistroPrediccionAusencia(cita_id=cita_id, riesgo="ALTO", timestamp_utc=timestamp, source="agenda")
        for cita_id in range(1, 22)
    ]
    queries.registrar_predicciones_ausencias("v2", many_items)
    ok = uc.ejecutar(ventana_dias=60)

    assert ok.estado_evaluacion == "OK"
    assert ok.mensaje_i18n_key == "prediccion_ausencias.resultados.estado.ok"
