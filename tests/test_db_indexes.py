from __future__ import annotations


def test_schema_crea_indices_de_busqueda_y_filtros(db_connection) -> None:
    expected = {
        "pacientes": "idx_pacientes_activo_apellidos_nombre",
        "medicos": "idx_medicos_activo_apellidos_nombre",
        "personal": "idx_personal_activo_apellidos_nombre",
        "citas": "idx_citas_activo_estado_inicio",
        "incidencias": "idx_incidencias_activo_estado_fecha",
    }

    for table, index_name in expected.items():
        indexes = {
            row["name"]
            for row in db_connection.execute(f"PRAGMA index_list('{table}')").fetchall()
        }
        assert index_name in indexes
