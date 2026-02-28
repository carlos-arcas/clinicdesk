from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from clinicdesk.app.application.demo_data.generator import (
    AppointmentGenerationConfig,
    generate_appointments,
    generate_doctors,
    generate_incidences,
    generate_patients,
    generate_personal,
)
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder


@dataclass(slots=True)
class SeedDemoDataRequest:
    seed: int = 123
    n_doctors: int = 10
    n_patients: int = 80
    n_appointments: int = 300
    from_date: str | None = None
    to_date: str | None = None
    incidence_rate: float = 0.15


@dataclass(slots=True)
class SeedDemoDataResponse:
    doctors: int
    patients: int
    personal: int
    appointments: int
    incidences: int
    from_date: str
    to_date: str
    dataset_version: str


class SeedDemoData:
    def __init__(self, seeder: DemoDataSeeder) -> None:
        self._seeder = seeder

    def execute(self, request: SeedDemoDataRequest) -> SeedDemoDataResponse:
        start_date, end_date = _resolve_dates(request.from_date, request.to_date)
        doctors = generate_doctors(request.n_doctors, request.seed)
        patients = generate_patients(request.n_patients, request.seed)
        staff = generate_personal(max(3, request.n_doctors // 2), request.seed)
        appointments = generate_appointments(
            patients,
            doctors,
            AppointmentGenerationConfig(
                n_appointments=request.n_appointments,
                from_date=start_date,
                to_date=end_date,
            ),
            request.seed,
        )
        incidences = generate_incidences(appointments, request.incidence_rate, request.seed)
        result = self._seeder.persist(doctors, patients, staff, appointments, incidences)
        return SeedDemoDataResponse(
            doctors=result.doctors,
            patients=result.patients,
            personal=result.personal,
            appointments=result.appointments,
            incidences=result.incidences,
            from_date=start_date.isoformat(),
            to_date=end_date.isoformat(),
            dataset_version=_dataset_version(request.seed),
        )


def _resolve_dates(from_date: str | None, to_date: str | None) -> tuple[date, date]:
    today = datetime.now().date()
    start = date.fromisoformat(from_date) if from_date else (today - timedelta(days=60))
    end = date.fromisoformat(to_date) if to_date else today
    if end < start:
        raise ValueError("Rango inválido: to_date no puede ser menor que from_date")
    return start, end


def _dataset_version(seed: int) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"demo_{stamp}_s{seed}"

