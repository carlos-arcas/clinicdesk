from __future__ import annotations

import sqlite3
from pathlib import Path

from clinicdesk.app.queries.dispensaciones_queries import DispensacionesQueries


def test_dispensaciones_queries_list_works_without_legacy_incidencia_column() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    _apply_schema(connection)
    _seed_minimum_data(connection)

    rows = DispensacionesQueries(connection).list(limit=10)

    assert len(rows) == 1
    assert rows[0].incidencia is True


def _apply_schema(connection: sqlite3.Connection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"
    connection.executescript(schema_path.read_text(encoding="utf-8"))
    connection.commit()


def _seed_minimum_data(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO pacientes (tipo_documento, documento, nombre, apellidos, activo) VALUES (?, ?, ?, ?, 1)",
        ("DNI", "100", "Ana", "Demo"),
    )
    connection.execute(
        "INSERT INTO medicos (tipo_documento, documento, nombre, apellidos, num_colegiado, especialidad, activo) VALUES (?, ?, ?, ?, ?, ?, 1)",
        ("DNI", "200", "Doc", "Demo", "COL-1", "General"),
    )
    connection.execute(
        "INSERT INTO personal (tipo_documento, documento, nombre, apellidos, puesto, activo) VALUES (?, ?, ?, ?, ?, 1)",
        ("DNI", "300", "Per", "Demo", "Enfermeria"),
    )
    connection.execute(
        "INSERT INTO medicamentos (nombre_compuesto, nombre_comercial, cantidad_en_almacen, activo) VALUES (?, ?, ?, 1)",
        ("Comp", "MedDemo", 10),
    )
    connection.execute(
        "INSERT INTO recetas (paciente_id, medico_id, fecha, observaciones, activo) VALUES (1, 1, '2026-01-01', '', 1)"
    )
    connection.execute(
        "INSERT INTO receta_lineas (receta_id, medicamento_id, dosis, duracion_dias, instrucciones, activo) VALUES (1, 1, '1', 3, 'cada 8h', 1)"
    )
    connection.execute(
        """
        INSERT INTO dispensaciones (
            receta_id, receta_linea_id, medicamento_id, personal_id,
            fecha_hora, cantidad, observaciones, activo
        ) VALUES (1, 1, 1, 1, '2026-01-02 10:00:00', 1, '', 1)
        """
    )
    connection.execute(
        """
        INSERT INTO incidencias (
            tipo, severidad, estado, fecha_hora, descripcion,
            dispensacion_id, confirmado_por_personal_id, nota_override, activo
        ) VALUES ('dispensacion', 'leve', 'abierta', '2026-01-02 10:01:00', 'test', 1, 1, 'ok', 1)
        """
    )
    connection.commit()
