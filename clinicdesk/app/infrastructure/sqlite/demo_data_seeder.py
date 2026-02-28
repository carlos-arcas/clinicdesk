from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from clinicdesk.app.application.demo_data.dtos import (
    AppointmentCreateDTO,
    DoctorCreateDTO,
    IncidenceDTO,
    PatientCreateDTO,
    PersonalCreateDTO,
)
from clinicdesk.app.domain.enums import EstadoCita, TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import Cita, Medico, Paciente, Personal, Sala
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia, IncidenciasRepository
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


class DemoDataSeeder:
    def __init__(
        self,
        connection: sqlite3.Connection,
        medicos_repo: MedicosRepository | None = None,
        pacientes_repo: PacientesRepository | None = None,
        personal_repo: PersonalRepository | None = None,
        salas_repo: SalasRepository | None = None,
        citas_repo: CitasRepository | None = None,
        incidencias_repo: IncidenciasRepository | None = None,
    ) -> None:
        self._medicos_repo = medicos_repo or MedicosRepository(connection)
        self._pacientes_repo = pacientes_repo or PacientesRepository(connection)
        self._personal_repo = personal_repo or PersonalRepository(connection)
        self._salas_repo = salas_repo or SalasRepository(connection)
        self._citas_repo = citas_repo or CitasRepository(connection)
        self._incidencias_repo = incidencias_repo or IncidenciasRepository(connection)

    def persist(
        self,
        doctors: list[DoctorCreateDTO],
        patients: list[PatientCreateDTO],
        staff: list[PersonalCreateDTO],
        appointments: list[AppointmentCreateDTO],
        incidences_by_appointment: dict[str, list[IncidenceDTO]],
    ) -> DemoSeedPersistResult:
        doctor_ids = [self._medicos_repo.create(_to_medico(dto)) for dto in doctors]
        patient_ids = [self._pacientes_repo.create(_to_paciente(dto)) for dto in patients]
        staff_ids = [self._personal_repo.create(_to_personal(dto)) for dto in staff]
        sala_ids = self._ensure_salas()
        appointment_id_map = self._persist_appointments(appointments, patient_ids, doctor_ids, sala_ids)
        incidences_count = self._persist_incidences(incidences_by_appointment, appointment_id_map, staff_ids)
        return DemoSeedPersistResult(
            doctors=len(doctor_ids),
            patients=len(patient_ids),
            personal=len(staff_ids),
            appointments=len(appointment_id_map),
            incidences=incidences_count,
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
    ) -> dict[str, int]:
        appointment_id_map: dict[str, int] = {}
        for dto in appointments:
            cita_id = self._citas_repo.create(
                Cita(
                    paciente_id=patient_ids[dto.patient_index],
                    medico_id=doctor_ids[dto.doctor_index],
                    sala_id=room_ids[(dto.patient_index + dto.doctor_index) % len(room_ids)],
                    inicio=dto.starts_at,
                    fin=dto.ends_at,
                    estado=EstadoCita(dto.status),
                    motivo=dto.reason,
                    notas=dto.notes,
                )
            )
            appointment_id_map[dto.external_id] = cita_id
        return appointment_id_map

    def _persist_incidences(
        self,
        incidences_by_appointment: dict[str, list[IncidenceDTO]],
        appointment_ids: dict[str, int],
        staff_ids: list[int],
    ) -> int:
        if not staff_ids:
            return 0
        total = 0
        for external_id, entries in incidences_by_appointment.items():
            cita_id = appointment_ids.get(external_id)
            if cita_id is None:
                continue
            for entry in entries:
                confirmer_id = staff_ids[cita_id % len(staff_ids)]
                self._incidencias_repo.create(
                    Incidencia(
                        tipo=entry.incidence_type,
                        severidad=entry.severity,
                        estado=entry.status,
                        fecha_hora=entry.occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
                        descripcion=entry.description,
                        cita_id=cita_id,
                        confirmado_por_personal_id=confirmer_id,
                        nota_override=entry.override_note,
                    )
                )
                total += 1
        return total


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
