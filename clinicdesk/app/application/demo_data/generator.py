from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from clinicdesk.app.application.demo_data.dtos import (
    AppointmentCreateDTO,
    DoctorCreateDTO,
    IncidenceDTO,
    PatientCreateDTO,
    PersonalCreateDTO,
)

_FIRST_NAMES = [
    "Lucia", "Mateo", "Sofia", "Hugo", "Valeria", "Leo", "Daniela", "Pablo", "Martina", "Alvaro",
    "Elena", "Nicolas", "Irene", "Diego", "Carmen", "Javier", "Marta", "Adrian", "Noa", "Andres",
]
_LAST_NAMES = [
    "Garcia", "Rodriguez", "Fernandez", "Lopez", "Martinez", "Sanchez", "Perez", "Gomez", "Martin",
    "Ruiz", "Diaz", "Moreno", "Alonso", "Navarro", "Torres", "Vazquez", "Castro", "Serrano", "Ortega", "Gil",
]
_SPECIALTIES = ["Medicina Familiar", "Pediatria", "Cardiologia", "Traumatologia", "Dermatologia", "Neurologia"]
_ROLES = ["Enfermeria", "Administracion", "Recepcion", "Auxiliar Clinico"]
_REASONS = ["Revision anual", "Control de dolor", "Seguimiento tratamiento", "Consulta urgente", "Primera valoracion"]
_NOTES = [
    "Paciente colaborador.",
    "Refiere molestias leves desde hace 3 dias.",
    "Se recomienda control en 2 semanas y analitica.",
    "Historia previa revisada; ajustar pauta progresivamente segun evolucion.",
]
_DURATIONS = [10, 20, 30, 45, 60]
_STATUS_WEIGHTS = (("CONFIRMADA", 45), ("REALIZADA", 35), ("CANCELADA", 12), ("NO_PRESENTADO", 8))


@dataclass(slots=True)
class AppointmentGenerationConfig:
    n_appointments: int
    from_date: date
    to_date: date
    weekend_ratio: float = 0.08
    outlier_ratio: float = 0.03


def generate_doctors(n: int, seed: int) -> list[DoctorCreateDTO]:
    rng = random.Random(seed)
    return [_build_doctor(i, rng) for i in range(n)]


def generate_patients(n: int, seed: int) -> list[PatientCreateDTO]:
    rng = random.Random(seed + 1_000)
    return [_build_patient(i, rng) for i in range(n)]


def generate_personal(n: int, seed: int) -> list[PersonalCreateDTO]:
    rng = random.Random(seed + 2_000)
    return [_build_personal(i, rng) for i in range(n)]


def generate_appointments(
    patients: list[PatientCreateDTO],
    doctors: list[DoctorCreateDTO],
    cfg: AppointmentGenerationConfig,
    seed: int,
) -> list[AppointmentCreateDTO]:
    if not patients or not doctors:
        return []
    if cfg.to_date < cfg.from_date:
        raise ValueError("Rango inválido para generación de citas.")
    rng = random.Random(seed + 3_000)
    return [_build_appointment(i, patients, doctors, cfg, rng) for i in range(cfg.n_appointments)]


def generate_incidences(
    appointments: list[AppointmentCreateDTO],
    rate: float,
    seed: int,
) -> dict[str, list[IncidenceDTO]]:
    rng = random.Random(seed + 4_000)
    incidence_map: dict[str, list[IncidenceDTO]] = {}
    for appt in appointments:
        if rng.random() > max(0.0, min(rate, 1.0)):
            continue
        incidence = IncidenceDTO(
            appointment_external_id=appt.external_id,
            incidence_type="CITA_FUERA_TURNO",
            severity="WARNING",
            status="ABIERTA",
            occurred_at=appt.starts_at,
            description=f"Cita {appt.external_id} con validacion manual para demo.",
            override_note="Override confirmado para dataset de demostracion.",
        )
        incidence_map.setdefault(appt.external_id, []).append(incidence)
    return incidence_map


def _build_doctor(index: int, rng: random.Random) -> DoctorCreateDTO:
    first_name, last_name = _pick_name_pair(index)
    return DoctorCreateDTO(
        document_type="DNI",
        document=f"{20_000_000 + index}",
        first_name=first_name,
        last_name=last_name,
        phone=_phone(index),
        email=f"{first_name.lower()}.{last_name.lower()}.{index}@clinicdesk.demo",
        birth_date=date(1968, 1, 1) + timedelta(days=rng.randint(0, 10_000)),
        address=f"Calle Salud {10 + index}",
        collegiate_number=f"COL-{9000 + index}",
        specialty=_SPECIALTIES[index % len(_SPECIALTIES)],
    )


def _build_patient(index: int, rng: random.Random) -> PatientCreateDTO:
    first_name, last_name = _pick_name_pair(index + 50)
    allergies = "Penicilina" if index % 9 == 0 else None
    observations = "Seguimiento de control." if index % 5 == 0 else None
    return PatientCreateDTO(
        document_type="DNI",
        document=f"{40_000_000 + index}",
        first_name=first_name,
        last_name=last_name,
        phone=_phone(index + 300),
        email=f"{first_name.lower()}.{last_name.lower()}.{index}@paciente.demo",
        birth_date=date(1945, 1, 1) + timedelta(days=rng.randint(0, 24_000)),
        address=f"Avenida Bienestar {20 + index}",
        allergies=allergies,
        observations=observations,
    )


def _build_personal(index: int, rng: random.Random) -> PersonalCreateDTO:
    first_name, last_name = _pick_name_pair(index + 100)
    return PersonalCreateDTO(
        document_type="DNI",
        document=f"{60_000_000 + index}",
        first_name=first_name,
        last_name=last_name,
        phone=_phone(index + 700),
        email=f"{first_name.lower()}.{last_name.lower()}.{index}@staff.demo",
        birth_date=date(1970, 1, 1) + timedelta(days=rng.randint(0, 15_000)),
        address=f"Paseo Clinica {5 + index}",
        role=_ROLES[index % len(_ROLES)],
        shift="Mañana" if index % 2 == 0 else "Tarde",
    )


def _build_appointment(
    index: int,
    patients: list[PatientCreateDTO],
    doctors: list[DoctorCreateDTO],
    cfg: AppointmentGenerationConfig,
    rng: random.Random,
) -> AppointmentCreateDTO:
    patient_index = rng.randrange(len(patients))
    doctor_index = rng.randrange(len(doctors))
    day = _pick_day(cfg, rng)
    starts_at = _build_start_datetime(day, rng)
    duration = _duration_minutes(cfg.outlier_ratio, rng)
    status = _weighted_status(rng)
    return AppointmentCreateDTO(
        external_id=f"APT-{index:05d}",
        patient_index=patient_index,
        doctor_index=doctor_index,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=duration),
        status=status,
        reason=_REASONS[index % len(_REASONS)],
        notes=_NOTES[index % len(_NOTES)] + (" " + "Detalle." * (index % 4)),
    )


def _pick_day(cfg: AppointmentGenerationConfig, rng: random.Random) -> date:
    day_count = (cfg.to_date - cfg.from_date).days + 1
    for _ in range(20):
        selected = cfg.from_date + timedelta(days=rng.randrange(day_count))
        if selected.weekday() < 5:
            return selected
        if rng.random() < cfg.weekend_ratio:
            return selected
    return cfg.from_date


def _build_start_datetime(day: date, rng: random.Random) -> datetime:
    hour = rng.choice([8, 9, 10, 11, 12, 15, 16, 17, 18])
    minute = rng.choice([0, 10, 20, 30, 40, 50])
    return datetime.combine(day, time(hour=hour, minute=minute))


def _duration_minutes(outlier_ratio: float, rng: random.Random) -> int:
    if rng.random() < max(0.0, min(outlier_ratio, 1.0)):
        return rng.choice([75, 90])
    return rng.choice(_DURATIONS)


def _weighted_status(rng: random.Random) -> str:
    values, weights = zip(*_STATUS_WEIGHTS)
    return rng.choices(values, weights=weights, k=1)[0]


def _pick_name_pair(index: int) -> tuple[str, str]:
    return _FIRST_NAMES[index % len(_FIRST_NAMES)], _LAST_NAMES[(index * 3) % len(_LAST_NAMES)]


def _phone(index: int) -> str:
    return f"6{10000000 + index:08d}"
