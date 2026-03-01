from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from clinicdesk.app.application.demo_data.dtos import (
    AppointmentCreateDTO,
    DoctorCreateDTO,
    IncidenceDTO,
    PatientCreateDTO,
    PersonalCreateDTO,
)
from clinicdesk.app.infrastructure.sqlite.demo_seed.appointments import persist_appointments_rows
from clinicdesk.app.infrastructure.sqlite.demo_seed.incidences import persist_incidences_rows
from clinicdesk.app.infrastructure.sqlite.demo_seed.orchestration import persist_demo_data
from clinicdesk.app.infrastructure.sqlite.demo_seed.people import persist_people
from clinicdesk.app.domain.enums import TipoSala
from clinicdesk.app.domain.modelos import Sala
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from clinicdesk.app.infrastructure.sqlite.repos_personal import PersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_salas import SalasRepository


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
        return persist_demo_data(
            seeder=self,
            doctors=doctors,
            patients=patients,
            staff=staff,
            appointments=appointments,
            incidences_by_appointment=incidences_by_appointment,
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
        return persist_people(
            self._medicos_repo,
            self._pacientes_repo,
            self._personal_repo,
            doctors,
            patients,
            staff,
        )

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
