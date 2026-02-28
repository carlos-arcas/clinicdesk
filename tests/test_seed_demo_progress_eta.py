from __future__ import annotations

import logging

from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData, SeedDemoDataRequest
from clinicdesk.app.bootstrap import bootstrap_database
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder


def test_seed_demo_logs_progress_with_eta(caplog, tmp_path) -> None:
    sqlite_path = tmp_path / "progress.db"
    connection = bootstrap_database(apply_schema=True, sqlite_path=sqlite_path.as_posix())
    caplog.set_level(logging.INFO)
    try:
        SeedDemoData(DemoDataSeeder(connection)).execute(
            SeedDemoDataRequest(seed=12, n_doctors=4, n_patients=20, n_appointments=100, batch_size=20)
        )
    finally:
        connection.close()

    progress_records = [record for record in caplog.records if record.getMessage() == "seed_progress"]
    assert progress_records
    sample = progress_records[0]
    assert isinstance(sample.done, int)
    assert isinstance(sample.total, int)
    assert isinstance(sample.eta_s, float)
    assert sample.total >= sample.done
