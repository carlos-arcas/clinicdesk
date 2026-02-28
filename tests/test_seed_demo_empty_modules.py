from __future__ import annotations

from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData, SeedDemoDataRequest
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder
from clinicdesk.app.queries.ausencias_queries import AusenciasQueries
from clinicdesk.app.queries.dispensaciones_queries import DispensacionesQueries
from clinicdesk.app.queries.materiales_queries import MaterialesQueries
from clinicdesk.app.queries.medicamentos_queries import MedicamentosQueries
from clinicdesk.app.queries.turnos_queries import TurnosQueries


def test_seed_demo_populates_empty_modules(db_connection):
    response = SeedDemoData(DemoDataSeeder(db_connection)).execute(SeedDemoDataRequest())
    assert response.medicamentos > 0
    assert response.materiales > 0
    assert response.dispensaciones > 0

    meds = MedicamentosQueries(db_connection).list_all(activo=True)
    materials = MaterialesQueries(db_connection).list_all(activo=True)
    dispensaciones = DispensacionesQueries(db_connection).list(limit=50)

    medico_id = db_connection.execute("SELECT id FROM medicos LIMIT 1").fetchone()[0]
    personal_id = db_connection.execute("SELECT id FROM personal LIMIT 1").fetchone()[0]
    turnos_med = TurnosQueries(db_connection).list_calendario_medico(medico_id, desde="2000-01-01", hasta="2100-01-01")
    aus_med = AusenciasQueries(db_connection).list_medico(medico_id, desde="2000-01-01", hasta="2100-01-01")
    aus_per = AusenciasQueries(db_connection).list_personal(personal_id, desde="2000-01-01", hasta="2100-01-01")

    assert len(meds) > 0
    assert len(materials) > 0
    assert len(dispensaciones) > 0
    assert len(turnos_med) > 0
    assert len(aus_med) > 0
    assert len(aus_per) > 0
