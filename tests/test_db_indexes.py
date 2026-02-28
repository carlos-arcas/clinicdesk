from __future__ import annotations

import sqlite3


def _indexes_for_table(con: sqlite3.Connection, table: str) -> set[str]:
    rows = con.execute(f"PRAGMA index_list('{table}')").fetchall()
    return {row[1] for row in rows}


def test_performance_indexes_are_created(db_connection: sqlite3.Connection) -> None:
    assert "idx_pacientes_activo_apellidos_nombre" in _indexes_for_table(db_connection, "pacientes")
    assert "idx_medicos_activo_apellidos_nombre" in _indexes_for_table(db_connection, "medicos")
    assert "idx_personal_activo_apellidos_nombre" in _indexes_for_table(db_connection, "personal")
    assert "idx_citas_activo_estado_inicio" in _indexes_for_table(db_connection, "citas")
    assert "idx_recetas_activo_estado_fecha" in _indexes_for_table(db_connection, "recetas")
    assert "idx_incidencias_activo_estado_fecha" in _indexes_for_table(db_connection, "incidencias")
