from __future__ import annotations

from datetime import datetime, timedelta, timezone

from clinicdesk.app.application.prediccion_ausencias.resultados_recientes import (
    DiagnosticoResultadosRecientes,
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


def _registrar_predicciones(queries: PrediccionAusenciasResultadosQueries, version: str, cita_ids: range, riesgo: str = "ALTO") -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    queries.registrar_predicciones_ausencias(
        version,
        [
            ItemRegistroPrediccionAusencia(cita_id=cita_id, riesgo=riesgo, timestamp_utc=timestamp, source="agenda")
            for cita_id in cita_ids
        ],
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


def test_obtener_diagnostico_resultados_recientes_cuenta_metricas(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    for cita_id in range(1, 26):
        estado = "NO_PRESENTADO" if cita_id % 2 == 0 else "REALIZADA"
        _insert_cita(
            db_connection,
            cita_id=cita_id,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            dias=4,
            estado=estado,
        )
    db_connection.commit()

    queries = PrediccionAusenciasResultadosQueries(db_connection)
    _registrar_predicciones(queries, "v1", range(1, 11))

    diagnostico = queries.obtener_diagnostico_resultados_recientes(ventana_dias=60)

    assert diagnostico.total_citas_cerradas_en_ventana == 25
    assert diagnostico.total_predicciones_registradas_en_ventana == 10
    assert diagnostico.total_predicciones_con_resultado == 10
    assert diagnostico.version_objetivo == "v1"


def test_uc_resultados_recientes_diagnostica_sin_citas_cerradas(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    for cita_id in range(1, 10):
        _insert_cita(
            db_connection,
            cita_id=cita_id,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            dias=2,
            estado="PENDIENTE",
        )
    db_connection.commit()

    uc = ObtenerResultadosRecientesPrediccionAusencias(PrediccionAusenciasResultadosQueries(db_connection), umbral_minimo=20)
    resultado = uc.ejecutar(ventana_dias=60)

    assert resultado.diagnostico is DiagnosticoResultadosRecientes.SIN_CITAS_CERRADAS


def test_uc_resultados_recientes_diagnostica_sin_predicciones_registradas(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    for cita_id in range(1, 22):
        _insert_cita(
            db_connection,
            cita_id=cita_id,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            dias=3,
            estado="REALIZADA",
        )
    db_connection.commit()

    uc = ObtenerResultadosRecientesPrediccionAusencias(PrediccionAusenciasResultadosQueries(db_connection), umbral_minimo=20)
    resultado = uc.ejecutar(ventana_dias=60)

    assert resultado.diagnostico is DiagnosticoResultadosRecientes.SIN_PREDICCIONES_REGISTRADAS


def test_uc_resultados_recientes_diagnostica_datos_insuficientes(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    for cita_id in range(1, 25):
        _insert_cita(
            db_connection,
            cita_id=cita_id,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            dias=6,
            estado="REALIZADA",
        )
    db_connection.commit()

    queries = PrediccionAusenciasResultadosQueries(db_connection)
    _registrar_predicciones(queries, "v1", range(1, 10))

    uc = ObtenerResultadosRecientesPrediccionAusencias(queries, umbral_minimo=20)
    resultado = uc.ejecutar(ventana_dias=60)

    assert resultado.diagnostico is DiagnosticoResultadosRecientes.DATOS_INSUFICIENTES


def test_uc_resultados_recientes_ok_devuelve_filas_por_riesgo(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    for cita_id in range(1, 31):
        estado = "NO_PRESENTADO" if cita_id % 3 == 0 else "REALIZADA"
        _insert_cita(
            db_connection,
            cita_id=cita_id,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            dias=8,
            estado=estado,
        )
    db_connection.commit()

    queries = PrediccionAusenciasResultadosQueries(db_connection)
    timestamp = datetime.now(timezone.utc).isoformat()
    queries.registrar_predicciones_ausencias(
        "v2",
        [
            ItemRegistroPrediccionAusencia(cita_id=idx, riesgo="ALTO", timestamp_utc=timestamp, source="agenda")
            for idx in range(1, 11)
        ]
        + [
            ItemRegistroPrediccionAusencia(cita_id=idx, riesgo="MEDIO", timestamp_utc=timestamp, source="agenda")
            for idx in range(11, 21)
        ]
        + [
            ItemRegistroPrediccionAusencia(cita_id=idx, riesgo="BAJO", timestamp_utc=timestamp, source="agenda")
            for idx in range(21, 31)
        ],
    )

    uc = ObtenerResultadosRecientesPrediccionAusencias(queries, umbral_minimo=20)
    resultado = uc.ejecutar(ventana_dias=60)

    assert resultado.diagnostico is DiagnosticoResultadosRecientes.OK
    assert [fila.riesgo for fila in resultado.filas] == ["BAJO", "MEDIO", "ALTO"]
    assert sum(fila.total_predichas for fila in resultado.filas) == 30
