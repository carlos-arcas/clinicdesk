from __future__ import annotations

import logging

from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData, SeedDemoDataRequest
from clinicdesk.app.bootstrap import bootstrap_database
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder
from clinicdesk.app.queries.pacientes_queries import PacientesQueries


def test_seed_demo_wiring_uses_same_sqlite_file(tmp_path) -> None:
    sqlite_path = tmp_path / "clinicdesk.db"
    write_connection = bootstrap_database(apply_schema=True, sqlite_path=sqlite_path.as_posix())
    try:
        response = SeedDemoData(DemoDataSeeder(write_connection)).execute(
            SeedDemoDataRequest(seed=77, n_doctors=2, n_patients=5, n_appointments=10)
        )
    finally:
        write_connection.close()

    assert response.patients == 5

    read_connection = bootstrap_database(apply_schema=True, sqlite_path=sqlite_path.as_posix())
    try:
        rows = PacientesQueries(read_connection).list_all()
    finally:
        read_connection.close()

    assert len(rows) > 0


def test_seed_demo_logs_progress(caplog) -> None:
    connection = bootstrap_database(apply_schema=True, sqlite_path=":memory:")
    caplog.set_level(logging.INFO)
    try:
        SeedDemoData(DemoDataSeeder(connection)).execute(
            SeedDemoDataRequest(seed=31, n_doctors=2, n_patients=4, n_appointments=12, batch_size=5)
        )
    finally:
        connection.close()

    messages = [record.getMessage() for record in caplog.records]
    assert any("Generating doctors" in message for message in messages)
    assert any("Persisting appointments batch" in message for message in messages)
    assert any("Seed demo total duration" in message for message in messages)
