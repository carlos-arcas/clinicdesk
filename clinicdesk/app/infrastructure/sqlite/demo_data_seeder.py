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
from clinicdesk.app.domain.modelos import Medico, Paciente, Personal, Sala
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from clinicdesk.app.infrastructure.sqlite.repos_personal import PersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_salas import SalasRepository
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
class _BatchProgress:
    phase: str
    total_items: int
    total_batches: int
    started_at: datetime

    def log_batch(self, batch_index: int, done: int) -> None:
        elapsed_s = max((datetime.now(UTC) - self.started_at).total_seconds(), 1e-6)
        rate = done / elapsed_s
        pending = max(0, self.total_items - done)
        eta_s = pending / rate if rate > 0 else 0.0
        LOGGER.info(
            "seed_progress",
            extra={
                "phase": self.phase,
                "batch_index": batch_index,
                "batch_total": self.total_batches,
                "done": done,
                "total": self.total_items,
                "elapsed_s": round(elapsed_s, 2),
                "rate": round(rate, 2),
                "eta_s": round(eta_s, 2),
            },
        )


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
        return _persist_demo_data(
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
        LOGGER.info("Persisting doctors... count=%s", len(doctors))
        doctor_ids = [self._medicos_repo.create(_to_medico(dto)) for dto in doctors]
        LOGGER.info("Persisting patients... count=%s", len(patients))
        patient_ids = [self._pacientes_repo.create(_to_paciente(dto)) for dto in patients]
        LOGGER.info("Persisting staff... count=%s", len(staff))
        staff_ids = [self._personal_repo.create(_to_personal(dto)) for dto in staff]
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


def _iter_batches(items: list, batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def persist_appointments_rows(
    connection: sqlite3.Connection,
    appointments: list[AppointmentCreateDTO],
    patient_ids: list[int],
    doctor_ids: list[int],
    room_ids: list[int],
    *,
    batch_size: int,
) -> dict[str, int]:
    appointment_id_map: dict[str, int] = {}
    total = len(appointments)
    if total == 0:
        return appointment_id_map
    total_batches = (total + batch_size - 1) // batch_size
    tracker = _BatchProgress("persist_appointments", total, total_batches, datetime.now(UTC))
    for batch_index, batch in enumerate(_iter_batches(appointments, batch_size), start=1):
        for dto in batch:
            cur = connection.execute(
                """
                INSERT INTO citas (
                    paciente_id, medico_id, sala_id, inicio, fin, estado, motivo, notas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_ids[dto.patient_index],
                    doctor_ids[dto.doctor_index],
                    room_ids[(dto.patient_index + dto.doctor_index) % len(room_ids)],
                    dto.starts_at,
                    dto.ends_at,
                    dto.status,
                    dto.reason,
                    dto.notes,
                ),
            )
            appointment_id_map[dto.external_id] = int(cur.lastrowid)
        connection.commit()
        tracker.log_batch(batch_index, len(appointment_id_map))
    return appointment_id_map


def persist_incidences_rows(
    connection: sqlite3.Connection,
    incidences_by_appointment: dict[str, list[IncidenceDTO]],
    appointment_ids: dict[str, int],
    staff_ids: list[int],
    *,
    batch_size: int,
) -> int:
    if not staff_ids:
        return 0
    total = 0
    flattened: list[tuple[int, IncidenceDTO]] = []
    for external_id, entries in incidences_by_appointment.items():
        cita_id = appointment_ids.get(external_id)
        if cita_id is None:
            continue
        for entry in entries:
            flattened.append((cita_id, entry))
    total_rows = len(flattened)
    if total_rows == 0:
        return 0
    total_batches = (total_rows + batch_size - 1) // batch_size
    tracker = _BatchProgress("persist_incidences", total_rows, total_batches, datetime.now(UTC))
    for batch_index, batch in enumerate(_iter_batches(flattened, batch_size), start=1):
        for cita_id, entry in batch:
            confirmer_id = staff_ids[cita_id % len(staff_ids)]
            connection.execute(
                """
                INSERT INTO incidencias (
                    tipo, severidad, estado, fecha_hora, descripcion,
                    cita_id, confirmado_por_personal_id, nota_override
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.incidence_type,
                    entry.severity,
                    entry.status,
                    entry.occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
                    entry.description,
                    cita_id,
                    confirmer_id,
                    entry.override_note or "seed-demo",
                ),
            )
            total += 1
        connection.commit()
        tracker.log_batch(batch_index, total)
    return total


def _persist_demo_data(
    *,
    seeder: DemoDataSeeder,
    doctors: list[DoctorCreateDTO],
    patients: list[PatientCreateDTO],
    staff: list[PersonalCreateDTO],
    appointments: list[AppointmentCreateDTO],
    incidences_by_appointment: dict[str, list[IncidenceDTO]],
    seed: int,
    from_date: date | None,
    to_date: date | None,
    n_medicamentos: int,
    n_materiales: int,
    n_recetas: int,
    n_movimientos: int,
    turns_months: int,
    n_ausencias: int,
    batch_size: int,
) -> DemoSeedPersistResult:
    safe_batch_size, from_date, to_date = seeder._normalize_persist_params(batch_size, from_date, to_date)
    doctor_ids, patient_ids, staff_ids = seeder._persist_people(doctors, patients, staff)
    sala_ids = seeder._ensure_salas()
    appointment_id_map = seeder._persist_appointments(
        appointments,
        patient_ids,
        doctor_ids,
        sala_ids,
        batch_size=safe_batch_size,
    )
    incidences_count = seeder._persist_incidences(
        incidences_by_appointment,
        appointment_id_map,
        staff_ids,
        batch_size=safe_batch_size,
    )
    meds_count, mat_count = seed_inventory(seeder._connection, n_medicamentos, n_materiales)
    recipes_count, line_count, disp_count = seed_recetas_dispensaciones(
        seeder._connection,
        patient_ids,
        doctor_ids,
        staff_ids,
        n_recetas,
        seed,
        from_date,
        to_date,
    )
    mov_med, mov_mat = seed_movimientos(seeder._connection, n_movimientos, staff_ids, seed, recipes_count > 0)
    turnos_count = seed_turnos_y_calendario(seeder._connection, doctor_ids, staff_ids, turns_months)
    ausencias_count = seed_ausencias(seeder._connection, doctor_ids, staff_ids, n_ausencias, seed)
    return seeder._build_result(
        doctor_ids=doctor_ids,
        patient_ids=patient_ids,
        staff_ids=staff_ids,
        appointment_id_map=appointment_id_map,
        incidences_count=incidences_count,
        meds_count=meds_count,
        mat_count=mat_count,
        recipes_count=recipes_count,
        line_count=line_count,
        disp_count=disp_count,
        mov_med=mov_med,
        mov_mat=mov_mat,
        turnos_count=turnos_count,
        ausencias_count=ausencias_count,
    )


def _to_medico(dto: DoctorCreateDTO) -> Medico:
    return Medico(
        tipo_documento=TipoDocumento(dto.document_type),
        documento=dto.document,
        nombre=dto.first_name,
        apellidos=dto.last_name,
        telefono=dto.phone,
        email=dto.email,
        fecha_nacimiento=dto.birth_date,
        direccion=dto.address,
        activo=True,
        num_colegiado=dto.collegiate_number,
        especialidad=dto.specialty,
    )


def _to_paciente(dto: PatientCreateDTO) -> Paciente:
    return Paciente(
        tipo_documento=TipoDocumento(dto.document_type),
        documento=dto.document,
        nombre=dto.first_name,
        apellidos=dto.last_name,
        telefono=dto.phone,
        email=dto.email,
        fecha_nacimiento=dto.birth_date,
        direccion=dto.address,
        activo=True,
        alergias=dto.allergies,
        observaciones=dto.observations,
    )


def _to_personal(dto: PersonalCreateDTO) -> Personal:
    return Personal(
        tipo_documento=TipoDocumento(dto.document_type),
        documento=dto.document,
        nombre=dto.first_name,
        apellidos=dto.last_name,
        telefono=dto.phone,
        email=dto.email,
        fecha_nacimiento=dto.birth_date,
        direccion=dto.address,
        activo=True,
        puesto=dto.role,
        turno=dto.shift,
    )
