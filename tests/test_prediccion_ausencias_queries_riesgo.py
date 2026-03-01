from __future__ import annotations

from datetime import datetime, timedelta

from clinicdesk.app.queries.prediccion_ausencias_queries import PrediccionAusenciasQueries


def _insertar_cita(db_connection, *, paciente_id: int, medico_id: int, sala_id: int, inicio: str, estado: str) -> None:
    db_connection.execute(
        """
        INSERT INTO citas (paciente_id, medico_id, sala_id, inicio, fin, estado, motivo, notas, activo)
        VALUES (?, ?, ?, ?, ?, ?, '', '', 1)
        """,
        (paciente_id, medico_id, sala_id, inicio, "2026-01-10 11:00:00", estado),
    )
    db_connection.commit()


def test_obtener_resumen_historial_paciente_cuenta_realizadas_y_no_presentadas(container, seed_data) -> None:
    _insertar_cita(
        container.connection,
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2025-12-01 10:00:00",
        estado="REALIZADA",
    )
    _insertar_cita(
        container.connection,
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2025-12-02 10:00:00",
        estado="NO_PRESENTADO",
    )

    queries = PrediccionAusenciasQueries(container.connection)
    resumen = queries.obtener_resumen_historial_paciente(seed_data["paciente_activo_id"])

    assert resumen.citas_realizadas == 1
    assert resumen.citas_no_presentadas == 1


def test_contar_citas_validas_recientes_aplica_ventana_dias(container, seed_data) -> None:
    ahora = datetime.now()
    _insertar_cita(
        container.connection,
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio=(ahora - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
        estado="REALIZADA",
    )
    _insertar_cita(
        container.connection,
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio=(ahora - timedelta(days=140)).strftime("%Y-%m-%d %H:%M:%S"),
        estado="NO_PRESENTADO",
    )

    queries = PrediccionAusenciasQueries(container.connection)

    assert queries.contar_citas_validas_recientes(90) == 1
