from __future__ import annotations

from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData, SeedDemoDataRequest
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder
from clinicdesk.app.infrastructure.sqlite.repos_seguimiento_operativo_ml import RepositorioSeguimientoOperativoMLSqlite
from clinicdesk.app.queries.ausencias_queries import AusenciasQueries
from clinicdesk.app.queries.confirmaciones_queries import ConfirmacionesQueries, FiltrosConfirmacionesQuery
from clinicdesk.app.queries.dashboard_gestion_queries import DashboardGestionQueries
from clinicdesk.app.queries.dispensaciones_queries import DispensacionesQueries
from clinicdesk.app.queries.materiales_queries import MaterialesQueries
from clinicdesk.app.queries.medicamentos_queries import MedicamentosQueries
from clinicdesk.app.queries.prediccion_ausencias_resultados_queries import PrediccionAusenciasResultadosQueries
from clinicdesk.app.queries.turnos_queries import TurnosQueries


def test_seed_demo_populates_empty_modules(db_connection):
    response = SeedDemoData(DemoDataSeeder(db_connection)).execute(SeedDemoDataRequest())
    assert response.medicamentos > 0
    assert response.materiales > 0
    assert response.dispensaciones > 0
    assert _count(db_connection, "recordatorios_citas") > 0
    assert _count(db_connection, "predicciones_ausencias_log") > 0
    assert _count(db_connection, "ml_acciones_operativas") > 0

    meds = MedicamentosQueries(db_connection).list_all(activo=True)
    materials = MaterialesQueries(db_connection).list_all(activo=True)
    dispensaciones = DispensacionesQueries(db_connection).list(limit=50)

    medico_id = db_connection.execute("SELECT id FROM medicos LIMIT 1").fetchone()[0]
    personal_id = db_connection.execute("SELECT id FROM personal LIMIT 1").fetchone()[0]
    cita_id = db_connection.execute("SELECT id FROM citas LIMIT 1").fetchone()[0]
    turnos_med = TurnosQueries(db_connection).list_calendario_medico(medico_id, desde="2000-01-01", hasta="2100-01-01")
    aus_med = AusenciasQueries(db_connection).list_medico(medico_id, desde="2000-01-01", hasta="2100-01-01")
    aus_per = AusenciasQueries(db_connection).list_personal(personal_id, desde="2000-01-01", hasta="2100-01-01")
    confirmaciones, _ = ConfirmacionesQueries(db_connection).buscar_citas_confirmaciones(
        FiltrosConfirmacionesQuery(desde="2000-01-01", hasta="2100-01-01"),
        limit=50,
        offset=0,
    )
    resultados_pred = PrediccionAusenciasResultadosQueries(db_connection).obtener_resultados_recientes_prediccion(
        ventana_dias=120
    )
    resumen = DashboardGestionQueries(db_connection).obtener_resumen_centro_salud(
        desde=_date("2000-01-01"),
        hasta=_date("2100-01-01"),
        medico_id=None,
        sala_id=None,
        estado=None,
    )
    historial_ml = RepositorioSeguimientoOperativoMLSqlite(db_connection).obtener_historial(str(cita_id))

    assert len(meds) > 0
    assert len(materials) > 0
    assert len(dispensaciones) > 0
    assert len(turnos_med) > 0
    assert len(aus_med) > 0
    assert len(aus_per) > 0
    assert any(row.recordatorio_estado_global != "SIN_PREPARAR" for row in confirmaciones)
    assert resultados_pred.version_modelo_fecha_utc is not None
    assert len(resultados_pred.filas) > 0
    assert resumen.riesgo_medio_pct is not None
    assert len(historial_ml) > 0


def _date(raw: str):
    from datetime import date

    return date.fromisoformat(raw)


def _count(db_connection, table: str) -> int:
    return int(db_connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
