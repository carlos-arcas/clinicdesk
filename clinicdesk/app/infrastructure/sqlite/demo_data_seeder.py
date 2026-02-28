from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from clinicdesk.app.application.demo_data.dtos import (
    AppointmentCreateDTO,
    DoctorCreateDTO,
    IncidenceDTO,
    PatientCreateDTO,
    PersonalCreateDTO,
)
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.domain.enums import TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import Sala
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from clinicdesk.app.infrastructure.sqlite.repos_personal import PersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_salas import SalasRepository
from clinicdesk.app.infrastructure.sqlite.demo_data_model_mappers import (
    to_medico,
    to_paciente,
    to_personal,
)
from clinicdesk.app.infrastructure.sqlite.demo_data_persistence import (
    persist_appointments_rows,
    persist_incidences_rows,
)
from clinicdesk.app.infrastructure.sqlite.demo_data_seed_helpers import (
    seed_ausencias,
    seed_inventory,
    seed_movimientos,
    seed_recetas_dispensaciones,
    seed_turnos_y_calendario,
)

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class DemoSeedPersistResult:
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




@dataclass(slots=True)
class _PersistOptions:
    seed: int
    from_date: date | None
    to_date: date | None
    n_medicamentos: int
    n_materiales: int
    n_recetas: int
    n_movimientos: int
    turns_months: int
    n_ausencias: int
    batch_size: int


class DemoDataSeeder:
    def __init__(
        self,
        connection: sqlite3.Connection,
        medicos_repo: MedicosRepository | None = None,
        pacientes_repo: PacientesRepository | None = None,
        personal_repo: PersonalRepository | None = None,
        salas_repo: SalasRepository | None = None,
    ) -> None:
        self._connection = connection
        self._medicos_repo = medicos_repo or MedicosRepository(connection)
        self._pacientes_repo = pacientes_repo or PacientesRepository(connection)
        self._personal_repo = personal_repo or PersonalRepository(connection)
        self._salas_repo = salas_repo or SalasRepository(connection)

    def persist(
        self,
        doctors: list[DoctorCreateDTO],
        patients: list[PatientCreateDTO],
        staff: list[PersonalCreateDTO],
        appointments: list[AppointmentCreateDTO],
        incidences_by_appointment: dict[str, list[IncidenceDTO]],
        *,
        seed: int = 123,
        from_date: date | None = None,
        to_date: date | None = None,
        n_medicamentos: int = 200,
        n_materiales: int = 120,
        n_recetas: int = 400,
        n_movimientos: int = 2000,
        turns_months: int = 2,
        n_ausencias: int = 60,
        batch_size: int = 500,
    ) -> DemoSeedPersistResult:
        options = _PersistOptions(
            seed=seed,
            from_date=from_date,
            to_date=to_date,
            n_medicamentos=n_medicamentos,
            n_materiales=n_materiales,
            n_recetas=n_recetas,
            n_movimientos=n_movimientos,
            turns_months=turns_months,
            n_ausencias=n_ausencias,
            batch_size=batch_size,
        )
        return _persist_demo_data(
            seeder=self,
            doctors=doctors,
            patients=patients,
            staff=staff,
            appointments=appointments,
            incidences_by_appointment=incidences_by_appointment,
            options=options,
        )

    def _normalize_persist_params(
        self,
        batch_size: int,
        from_date: date | None,
        to_date: date | None,
    ) -> tuple[int, date, date]:
        return max(1, batch_size), from_date or (date.today() - timedelta(days=30)), to_date or date.today()

    def _persist_people(
        self,
        doctors: list[DoctorCreateDTO],
        patients: list[PatientCreateDTO],
        staff: list[PersonalCreateDTO],
    ) -> tuple[list[int], list[int], list[int]]:
        LOGGER.info("Persisting doctors... count=%s", len(doctors))
        doctor_ids = [self._medicos_repo.create(to_medico(dto)) for dto in doctors]
        LOGGER.info("Persisting patients... count=%s", len(patients))
        patient_ids = [self._pacientes_repo.create(to_paciente(dto)) for dto in patients]
        LOGGER.info("Persisting staff... count=%s", len(staff))
        staff_ids = [self._personal_repo.create(to_personal(dto)) for dto in staff]
        return doctor_ids, patient_ids, staff_ids

    def _build_result(
        self,
        *,
        doctor_ids: list[int],
        patient_ids: list[int],
        staff_ids: list[int],
        appointment_id_map: dict[str, int],
        incidences_count: int,
        meds_count: int,
        mat_count: int,
        recipes_count: int,
        line_count: int,
        disp_count: int,
        mov_med: int,
        mov_mat: int,
        turnos_count: int,
        ausencias_count: int,
    ) -> DemoSeedPersistResult:
        return DemoSeedPersistResult(
            doctors=len(doctor_ids),
            patients=len(patient_ids),
            personal=len(staff_ids),
            appointments=len(appointment_id_map),
            incidences=incidences_count,
            medicamentos=meds_count,
            materiales=mat_count,
            recetas=recipes_count,
            receta_lineas=line_count,
            dispensaciones=disp_count,
            movimientos_medicamentos=mov_med,
            movimientos_materiales=mov_mat,
            turnos=turnos_count,
            ausencias=ausencias_count,
        )

    def _ensure_salas(self) -> list[int]:
        rooms = self._salas_repo.list_all(solo_activas=True)
        if rooms:
            return [room.id for room in rooms if room.id is not None]
        defaults = [
            Sala(nombre="Consulta Demo 1", tipo=TipoSala.CONSULTA, ubicacion="Planta 1", activa=True),
            Sala(nombre="Consulta Demo 2", tipo=TipoSala.CONSULTA, ubicacion="Planta 1", activa=True),
            Sala(nombre="Box Demo", tipo=TipoSala.FISIOTERAPIA, ubicacion="Planta 2", activa=True),
        ]
        return [self._salas_repo.create(room) for room in defaults]

    def _persist_appointments(
        self,
        appointments: list[AppointmentCreateDTO],
        patient_ids: list[int],
        doctor_ids: list[int],
        room_ids: list[int],
        *,
        batch_size: int,
    ) -> dict[str, int]:
        return persist_appointments_rows(
            self._connection,
            appointments,
            patient_ids,
            doctor_ids,
            room_ids,
            batch_size=batch_size,
        )

    def _persist_incidences(
        self,
        incidences_by_appointment: dict[str, list[IncidenceDTO]],
        appointment_ids: dict[str, int],
        staff_ids: list[int],
        *,
        batch_size: int,
    ) -> int:
        return persist_incidences_rows(
            self._connection,
            incidences_by_appointment,
            appointment_ids,
            staff_ids,
            batch_size=batch_size,
        )


def _persist_demo_data(
    *,
    seeder: DemoDataSeeder,
    doctors: list[DoctorCreateDTO],
    patients: list[PatientCreateDTO],
    staff: list[PersonalCreateDTO],
    appointments: list[AppointmentCreateDTO],
    incidences_by_appointment: dict[str, list[IncidenceDTO]],
    options: _PersistOptions,
) -> DemoSeedPersistResult:
    safe_batch_size, from_date, to_date = seeder._normalize_persist_params(
        options.batch_size,
        options.from_date,
        options.to_date,
    )
    doctor_ids, patient_ids, staff_ids = seeder._persist_people(doctors, patients, staff)
    appointment_id_map, incidences_count = _persist_clinical_records(
        seeder=seeder,
        appointments=appointments,
        incidences_by_appointment=incidences_by_appointment,
        patient_ids=patient_ids,
        doctor_ids=doctor_ids,
        staff_ids=staff_ids,
        batch_size=safe_batch_size,
    )
    operational_counts = _seed_operational_modules(
        connection=seeder._connection,
        patient_ids=patient_ids,
        doctor_ids=doctor_ids,
        staff_ids=staff_ids,
        n_medicamentos=options.n_medicamentos,
        n_materiales=options.n_materiales,
        n_recetas=options.n_recetas,
        n_movimientos=options.n_movimientos,
        turns_months=options.turns_months,
        n_ausencias=options.n_ausencias,
        seed=options.seed,
        from_date=from_date,
        to_date=to_date,
    )
    return _build_persist_result(
        seeder=seeder,
        doctor_ids=doctor_ids,
        patient_ids=patient_ids,
        staff_ids=staff_ids,
        appointment_id_map=appointment_id_map,
        incidences_count=incidences_count,
        operational_counts=operational_counts,
    )


def _persist_clinical_records(
    *,
    seeder: DemoDataSeeder,
    appointments: list[AppointmentCreateDTO],
    incidences_by_appointment: dict[str, list[IncidenceDTO]],
    patient_ids: list[int],
    doctor_ids: list[int],
    staff_ids: list[int],
    batch_size: int,
) -> tuple[dict[str, int], int]:
    sala_ids = seeder._ensure_salas()
    appointment_id_map = seeder._persist_appointments(
        appointments,
        patient_ids,
        doctor_ids,
        sala_ids,
        batch_size=batch_size,
    )
    incidences_count = seeder._persist_incidences(
        incidences_by_appointment,
        appointment_id_map,
        staff_ids,
        batch_size=batch_size,
    )
    return appointment_id_map, incidences_count


def _build_persist_result(
    *,
    seeder: DemoDataSeeder,
    doctor_ids: list[int],
    patient_ids: list[int],
    staff_ids: list[int],
    appointment_id_map: dict[str, int],
    incidences_count: int,
    operational_counts: tuple[int, int, int, int, int, int, int, int, int],
) -> DemoSeedPersistResult:
    return seeder._build_result(
        doctor_ids=doctor_ids,
        patient_ids=patient_ids,
        staff_ids=staff_ids,
        appointment_id_map=appointment_id_map,
        incidences_count=incidences_count,
        meds_count=operational_counts[0],
        mat_count=operational_counts[1],
        recipes_count=operational_counts[2],
        line_count=operational_counts[3],
        disp_count=operational_counts[4],
        mov_med=operational_counts[5],
        mov_mat=operational_counts[6],
        turnos_count=operational_counts[7],
        ausencias_count=operational_counts[8],
    )


def _seed_operational_modules(
    *,
    connection: sqlite3.Connection,
    patient_ids: list[int],
    doctor_ids: list[int],
    staff_ids: list[int],
    n_medicamentos: int,
    n_materiales: int,
    n_recetas: int,
    n_movimientos: int,
    turns_months: int,
    n_ausencias: int,
    seed: int,
    from_date: date,
    to_date: date,
) -> tuple[int, int, int, int, int, int, int, int, int]:
    meds_count, mat_count = seed_inventory(connection, n_medicamentos, n_materiales)
    recipes_count, line_count, disp_count = seed_recetas_dispensaciones(
        connection,
        patient_ids,
        doctor_ids,
        staff_ids,
        n_recetas,
        seed,
        from_date,
        to_date,
    )
    mov_med, mov_mat = seed_movimientos(connection, n_movimientos, staff_ids, seed, recipes_count > 0)
    turnos_count = seed_turnos_y_calendario(connection, doctor_ids, staff_ids, turns_months)
    ausencias_count = seed_ausencias(connection, doctor_ids, staff_ids, n_ausencias, seed)
    return (
        meds_count,
        mat_count,
        recipes_count,
        line_count,
        disp_count,
        mov_med,
        mov_mat,
        turnos_count,
        ausencias_count,
    )
