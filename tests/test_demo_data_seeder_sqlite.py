from __future__ import annotations

import sqlite3
from pathlib import Path

from clinicdesk.app.application.demo_data.generator import (
    AppointmentGenerationConfig,
    generate_appointments,
    generate_doctors,
    generate_incidences,
    generate_patients,
    generate_personal,
)
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder


def test_demo_data_seeder_persists_coherent_counts() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    _apply_schema(connection)

    doctors = generate_doctors(4, 91)
    patients = generate_patients(10, 91)
    staff = generate_personal(3, 91)
    appointments = generate_appointments(
        patients,
        doctors,
        AppointmentGenerationConfig(n_appointments=60, from_date=_date("2026-01-01"), to_date=_date("2026-02-28")),
        91,
    )
    incidences = generate_incidences(appointments, rate=0.2, seed=91)

    result = DemoDataSeeder(connection).persist(doctors, patients, staff, appointments, incidences)

    assert result.doctors == 4
    assert result.patients == 10
    assert result.personal == 3
    assert result.appointments == 60
    assert result.incidences > 0
    assert _count(connection, "medicos") == 4
    assert _count(connection, "pacientes") == 10
    assert _count(connection, "personal") == 3
    assert _count(connection, "citas") == 60
    assert _count(connection, "incidencias") == result.incidences


def _apply_schema(connection: sqlite3.Connection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"
    connection.executescript(schema_path.read_text(encoding="utf-8"))
    connection.commit()


def _count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) as total FROM {table}").fetchone()["total"])


def _date(raw: str):
    from datetime import date

    return date.fromisoformat(raw)
