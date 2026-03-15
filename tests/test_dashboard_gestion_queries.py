from __future__ import annotations

from clinicdesk.app.queries.dashboard_gestion_queries import DashboardGestionQueries


def test_listar_salas_filtro_usa_columna_activa_schema_real(db_connection) -> None:
    db_connection.execute("INSERT INTO salas(nombre, tipo, ubicacion, activa) VALUES ('Sala A', 'CONSULTA', 'P1', 1)")
    db_connection.execute("INSERT INTO salas(nombre, tipo, ubicacion, activa) VALUES ('Sala B', 'CONSULTA', 'P1', 0)")
    db_connection.commit()

    rows = DashboardGestionQueries(db_connection).listar_salas_filtro()

    assert [row.etiqueta for row in rows] == ["Sala A"]
