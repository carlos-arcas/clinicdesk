from __future__ import annotations

from datetime import date

import pytest

from clinicdesk.app.application.usecases.obtener_metricas_operativas import ObtenerMetricasOperativas
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.queries.metricas_operativas_queries import MetricasOperativasQueries


def test_obtener_metricas_operativas_calcula_kpis_y_descartados(db_connection) -> None:
    _seed_catalogos_minimos(db_connection)
    _seed_citas_metricas(db_connection)
    use_case = ObtenerMetricasOperativas(MetricasOperativasQueries(db_connection))

    resultado = use_case.execute(date(2025, 1, 10), date(2025, 1, 10))

    assert len(resultado.por_dia) == 1
    fila_dia = resultado.por_dia[0]
    assert fila_dia.fecha == "2025-01-10"
    assert fila_dia.total_citas == 3
    assert fila_dia.espera_media_min == 10.0
    assert fila_dia.consulta_media_min == 22.5
    assert fila_dia.total_clinica_media_min == 60.0
    assert fila_dia.retraso_media_min == 5.0
    assert fila_dia.descartados == 1

    assert len(resultado.por_medico) == 2
    por_medico = {item.medico_id: item for item in resultado.por_medico}
    assert por_medico[1].total_citas == 2
    assert por_medico[1].espera_media_min == 10.0
    assert por_medico[1].consulta_media_min == 30.0
    assert por_medico[1].retraso_media_min == 5.0
    assert por_medico[2].total_citas == 1
    assert por_medico[2].espera_media_min is None
    assert por_medico[2].consulta_media_min == 15.0
    assert por_medico[2].retraso_media_min == 5.0


def test_metricas_operativas_restringe_rango_maximo(db_connection) -> None:
    use_case = ObtenerMetricasOperativas(MetricasOperativasQueries(db_connection), max_dias_rango=90)

    with pytest.raises(ValidationError):
        use_case.execute(date(2025, 1, 1), date(2025, 4, 1))


def _seed_catalogos_minimos(db_connection) -> None:
    db_connection.execute(
        """
        INSERT INTO pacientes (id, tipo_documento, documento, nombre, apellidos, activo)
        VALUES (1, 'DNI', 'P1', 'Ana', 'Paciente', 1)
        """
    )
    db_connection.execute(
        """
        INSERT INTO medicos (id, tipo_documento, documento, nombre, apellidos, activo, num_colegiado, especialidad)
        VALUES
            (1, 'DNI', 'M1', 'Laura', 'Lopez', 1, 'COL-1', 'General'),
            (2, 'DNI', 'M2', 'Mario', 'Diaz', 1, 'COL-2', 'General')
        """
    )
    db_connection.execute(
        """
        INSERT INTO salas (id, nombre, tipo, activa)
        VALUES (1, 'Consulta 1', 'CONSULTA', 1)
        """
    )
    db_connection.commit()


def _seed_citas_metricas(db_connection) -> None:
    db_connection.execute(
        """
        INSERT INTO citas (
            id, paciente_id, medico_id, sala_id, inicio, fin, estado, activo,
            check_in_at, llamado_a_consulta_at, consulta_inicio_at, consulta_fin_at, check_out_at
        ) VALUES (
            1, 1, 1, 1, '2025-01-10 10:00:00', '2025-01-10 10:30:00', 'REALIZADA', 1,
            '2025-01-10 09:50:00', '2025-01-10 10:00:00', '2025-01-10 10:05:00', '2025-01-10 10:35:00', '2025-01-10 10:50:00'
        )
        """
    )
    db_connection.execute(
        """
        INSERT INTO citas (
            id, paciente_id, medico_id, sala_id, inicio, fin, estado, activo,
            check_in_at, llamado_a_consulta_at, consulta_inicio_at, consulta_fin_at, check_out_at
        ) VALUES (
            2, 1, 1, 1, '2025-01-10 12:00:00', '2025-01-10 12:30:00', 'REALIZADA', 1,
            '2025-01-10 12:00:00', '2025-01-10 11:50:00', '2025-01-10 11:50:00', '2025-01-10 11:40:00', '2025-01-10 11:40:00'
        )
        """
    )
    db_connection.execute(
        """
        INSERT INTO citas (
            id, paciente_id, medico_id, sala_id, inicio, fin, estado, activo,
            check_in_at, llamado_a_consulta_at, consulta_inicio_at, consulta_fin_at, check_out_at
        ) VALUES (
            3, 1, 2, 1, '2025-01-10 11:00:00', '2025-01-10 11:30:00', 'NO_PRESENTADO', 1,
            NULL, NULL, '2025-01-10 11:05:00', '2025-01-10 11:20:00', NULL
        )
        """
    )
    db_connection.commit()
