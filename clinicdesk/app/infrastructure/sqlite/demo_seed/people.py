from __future__ import annotations

from clinicdesk.app.application.demo_data.dtos import DoctorCreateDTO, PatientCreateDTO, PersonalCreateDTO
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Medico, Paciente, Personal
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from clinicdesk.app.infrastructure.sqlite.repos_personal import PersonalRepository

LOGGER = get_logger(__name__)


def persist_people(
    medicos_repo: MedicosRepository,
    pacientes_repo: PacientesRepository,
    personal_repo: PersonalRepository,
    doctors: list[DoctorCreateDTO],
    patients: list[PatientCreateDTO],
    staff: list[PersonalCreateDTO],
) -> tuple[list[int], list[int], list[int]]:
    LOGGER.info("Persisting doctors... count=%s", len(doctors))
    doctor_ids = [medicos_repo.create(_to_medico(dto)) for dto in doctors]
    LOGGER.info("Persisting patients... count=%s", len(patients))
    patient_ids = [pacientes_repo.create(_to_paciente(dto)) for dto in patients]
    LOGGER.info("Persisting staff... count=%s", len(staff))
    staff_ids = [personal_repo.create(_to_personal(dto)) for dto in staff]
    return doctor_ids, patient_ids, staff_ids


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
