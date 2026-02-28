from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.application.demo_data.generator import (
    AppointmentGenerationConfig,
    generate_appointments,
    generate_doctors,
    generate_incidences,
    generate_patients,
    generate_personal,
)
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class SeedDemoDataRequest:
    seed: int = 123
    n_doctors: int = 10
    n_patients: int = 80
    n_appointments: int = 300
    from_date: str | None = None
    to_date: str | None = None
    incidence_rate: float = 0.15
    batch_size: int = 500
    n_medicamentos: int = 200
    n_materiales: int = 120
    n_recetas: int = 400
    n_movimientos: int = 2000
    turns_months: int = 2
    n_ausencias: int = 60


@dataclass(slots=True)
class SeedDemoDataResponse:
    doctors: int
    patients: int
    personal: int
    appointments: int
    incidences: int
    medicamentos: int
    materiales: int
    recetas: int
    receta_lineas: int
    dispensaciones: int
    movimientos_medicamentos: int
    movimientos_materiales: int
    turnos: int
    ausencias: int
    from_date: str
    to_date: str
    dataset_version: str


class SeedDemoData:
    def __init__(self, seeder: DemoDataSeeder) -> None:
        self._seeder = seeder

    def execute(self, request: SeedDemoDataRequest) -> SeedDemoDataResponse:
        started_at = datetime.now(UTC)
        start_date, end_date = _resolve_dates(request.from_date, request.to_date)
        LOGGER.info("Generating doctors... count=%s", request.n_doctors)
        doctors = generate_doctors(request.n_doctors, request.seed)
        LOGGER.info("Generating patients... count=%s", request.n_patients)
        patients = generate_patients(request.n_patients, request.seed)
        LOGGER.info("Generating staff... count=%s", max(3, request.n_doctors // 2))
        staff = generate_personal(max(3, request.n_doctors // 2), request.seed)
        LOGGER.info("Generating appointments... count=%s", request.n_appointments)
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
        LOGGER.info("Generating incidences... rate=%.3f", request.incidence_rate)
        incidences = generate_incidences(appointments, request.incidence_rate, request.seed)
        generation_seconds = (datetime.now(UTC) - started_at).total_seconds()
        LOGGER.info("Generation done in %.2fs", generation_seconds)
        persist_started = datetime.now(UTC)
        result = self._seeder.persist(
            doctors,
            patients,
            staff,
            appointments,
            incidences,
            seed=request.seed,
            from_date=start_date,
            to_date=end_date,
            n_medicamentos=request.n_medicamentos,
            n_materiales=request.n_materiales,
            n_recetas=request.n_recetas,
            n_movimientos=request.n_movimientos,
            turns_months=request.turns_months,
            n_ausencias=request.n_ausencias,
            batch_size=request.batch_size,
        )
        persist_seconds = (datetime.now(UTC) - persist_started).total_seconds()
        total_seconds = (datetime.now(UTC) - started_at).total_seconds()
        LOGGER.info("Persisting done in %.2fs", persist_seconds)
        LOGGER.info("Seed demo total duration %.2fs", total_seconds)
        return SeedDemoDataResponse(
            doctors=result.doctors,
            patients=result.patients,
            personal=result.personal,
            appointments=result.appointments,
            incidences=result.incidences,
            medicamentos=result.medicamentos,
            materiales=result.materiales,
            recetas=result.recetas,
            receta_lineas=result.receta_lineas,
            dispensaciones=result.dispensaciones,
            movimientos_medicamentos=result.movimientos_medicamentos,
            movimientos_materiales=result.movimientos_materiales,
            turnos=result.turnos,
            ausencias=result.ausencias,
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
