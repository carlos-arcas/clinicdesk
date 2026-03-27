from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from clinicdesk.app.application.demo_data.catalogos import (
    ALERGIAS_FRECUENTES,
    APELLIDOS,
    DOMINIOS_CLINICA,
    DOMINIOS_CONTACTO,
    ESPECIALIDADES,
    MUNICIPIOS,
    NOMBRES,
    NOTAS_CITA,
    OBSERVACIONES_PACIENTE,
    PUESTOS_PERSONAL,
    VIAS,
)
from clinicdesk.app.application.demo_data.dtos import (
    AppointmentCreateDTO,
    DoctorCreateDTO,
    IncidenceDTO,
    PatientCreateDTO,
    PersonalCreateDTO,
)

_DURACIONES_BASE = (15, 20, 30, 40, 45)
_LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"
_PLANTILLAS_INCIDENCIA = (
    (
        "RETRASO_EN_AGENDA",
        "WARNING",
        "EN_REVISION",
        "Recepcion documenta retraso de agenda y reajuste de la cola asistencial.",
        "Se confirma el cambio con el paciente antes de mantener la cita.",
    ),
    (
        "DOCUMENTACION_INCOMPLETA",
        "INFO",
        "RESUELTA",
        "Faltaba informe clinico de apoyo y se completa antes de la consulta.",
        "Personal administrativo valida la documentacion en mostrador.",
    ),
    (
        "PACIENTE_NO_LOCALIZADO",
        "WARNING",
        "ABIERTA",
        "No se consigue confirmacion por el canal habitual en el recordatorio previo.",
        "Se deja nota operativa para segundo intento de contacto.",
    ),
    (
        "CAMBIO_DE_SALA",
        "INFO",
        "RESUELTA",
        "La cita se reubica por ajuste interno de disponibilidad de sala.",
        "El cambio se comunica y queda trazado en la agenda.",
    ),
)

@dataclass(slots=True)
class AppointmentGenerationConfig:
    n_appointments: int
    from_date: date
    to_date: date
    weekend_ratio: float = 0.08
    outlier_ratio: float = 0.03
    reference_date: date | None = None


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
        raise ValueError("Rango invalido para generacion de citas.")
    rng = random.Random(seed + 3_000)
    reference_date = cfg.reference_date or date.today()
    return [
        _build_appointment(i, patients, doctors, cfg, reference_date, rng)
        for i in range(cfg.n_appointments)
    ]


def generate_incidences(
    appointments: list[AppointmentCreateDTO],
    rate: float,
    seed: int,
) -> dict[str, list[IncidenceDTO]]:
    rng = random.Random(seed + 4_000)
    incidence_map: dict[str, list[IncidenceDTO]] = {}
    safe_rate = max(0.0, min(rate, 1.0))
    for appt in appointments:
        if rng.random() > safe_rate:
            continue
        tipo, severidad, estado, descripcion, override_note = _pick_incidence_template(appt, rng)
        incidence = IncidenceDTO(
            appointment_external_id=appt.external_id,
            incidence_type=tipo,
            severity=severidad,
            status=estado,
            occurred_at=appt.starts_at,
            description=f"{descripcion} Referencia agenda {appt.starts_at:%d/%m %H:%M}.",
            override_note=override_note,
        )
        incidence_map.setdefault(appt.external_id, []).append(incidence)
    return incidence_map


def _build_doctor(index: int, rng: random.Random) -> DoctorCreateDTO:
    first_name, last_name = _pick_name_pair(index, rng)
    specialty = ESPECIALIDADES[index % len(ESPECIALIDADES)].nombre
    return DoctorCreateDTO(
        document_type="DNI",
        document=_dni(index, base=20_000_000),
        first_name=first_name,
        last_name=last_name,
        phone=_phone(index),
        email=_build_email(first_name, last_name, index, DOMINIOS_CLINICA),
        birth_date=date(1968, 1, 1) + timedelta(days=rng.randint(0, 10_000)),
        address=_build_address(index, rng),
        collegiate_number=f"28/{90_000 + index}",
        specialty=specialty,
    )


def _build_patient(index: int, rng: random.Random) -> PatientCreateDTO:
    first_name, last_name = _pick_name_pair(index + 50, rng)
    return PatientCreateDTO(
        document_type="DNI",
        document=_dni(index, base=40_000_000),
        first_name=first_name,
        last_name=last_name,
        phone=_phone(index + 300) if rng.random() > 0.08 else "",
        email=_build_email(first_name, last_name, index, DOMINIOS_CONTACTO) if rng.random() > 0.18 else "",
        birth_date=date(1945, 1, 1) + timedelta(days=rng.randint(0, 24_000)),
        address=_build_address(index + 80, rng),
        allergies=_pick_optional(ALERGIAS_FRECUENTES, rng, threshold=0.15),
        observations=_pick_optional(OBSERVACIONES_PACIENTE, rng, threshold=0.22),
    )


def _build_personal(index: int, rng: random.Random) -> PersonalCreateDTO:
    first_name, last_name = _pick_name_pair(index + 100, rng)
    return PersonalCreateDTO(
        document_type="DNI",
        document=_dni(index, base=60_000_000),
        first_name=first_name,
        last_name=last_name,
        phone=_phone(index + 700),
        email=_build_email(first_name, last_name, index, DOMINIOS_CLINICA),
        birth_date=date(1970, 1, 1) + timedelta(days=rng.randint(0, 15_000)),
        address=_build_address(index + 140, rng),
        role=PUESTOS_PERSONAL[index % len(PUESTOS_PERSONAL)],
        shift="Manana" if index % 2 == 0 else "Tarde",
    )


def _build_appointment(
    index: int,
    patients: list[PatientCreateDTO],
    doctors: list[DoctorCreateDTO],
    cfg: AppointmentGenerationConfig,
    reference_date: date,
    rng: random.Random,
) -> AppointmentCreateDTO:
    patient_index = _pick_patient_index(len(patients), rng)
    doctor_index = _pick_doctor_index(len(doctors), patient_index, rng)
    day = _pick_day(cfg, rng)
    starts_at = _build_start_datetime(day, rng)
    reason = _pick_reason(doctors[doctor_index].specialty, rng)
    duration = _duration_minutes(reason, cfg.outlier_ratio, rng)
    status = _weighted_status(day, starts_at, reference_date, rng)
    return AppointmentCreateDTO(
        external_id=f"APT-{index:05d}",
        patient_index=patient_index,
        doctor_index=doctor_index,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=duration),
        status=status,
        reason=reason,
        notes=_build_notes(reason, status, rng),
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
    hour = rng.choice([8, 9, 10, 11, 12, 15, 16, 17, 18, 19])
    minute = rng.choice([0, 15, 30, 45])
    return datetime.combine(day, time(hour=hour, minute=minute))


def _duration_minutes(reason: str, outlier_ratio: float, rng: random.Random) -> int:
    if rng.random() < max(0.0, min(outlier_ratio, 1.0)):
        return rng.choice([75, 90])
    if any(token in reason.lower() for token in ("valoracion", "lesion", "dolor", "palpitaciones")):
        return rng.choice([30, 40, 45, 60])
    return rng.choice(_DURACIONES_BASE)


def _weighted_status(day: date, starts_at: datetime, reference_date: date, rng: random.Random) -> str:
    delta = (day - reference_date).days
    if delta < 0:
        values, weights = zip(
            ("REALIZADA", 68),
            ("NO_PRESENTADO", 14),
            ("CANCELADA", 10),
            ("CONFIRMADA", 5),
            ("PROGRAMADA", 3),
        )
    elif delta == 0 and starts_at.hour < 14:
        values, weights = zip(
            ("REALIZADA", 30),
            ("EN_CURSO", 28),
            ("CONFIRMADA", 20),
            ("PROGRAMADA", 10),
            ("NO_PRESENTADO", 7),
            ("CANCELADA", 5),
        )
    elif delta == 0:
        values, weights = zip(
            ("CONFIRMADA", 42),
            ("EN_CURSO", 18),
            ("PROGRAMADA", 28),
            ("CANCELADA", 7),
            ("REALIZADA", 5),
        )
    else:
        values, weights = zip(("CONFIRMADA", 56), ("PROGRAMADA", 34), ("CANCELADA", 10))
    return rng.choices(values, weights=weights, k=1)[0]


def _pick_name_pair(index: int, rng: random.Random) -> tuple[str, str]:
    first_name = NOMBRES[(index + rng.randrange(len(NOMBRES))) % len(NOMBRES)]
    last_a = APELLIDOS[(index * 2 + rng.randrange(len(APELLIDOS))) % len(APELLIDOS)]
    last_b = APELLIDOS[(index * 5 + rng.randrange(len(APELLIDOS))) % len(APELLIDOS)]
    if last_a == last_b:
        last_b = APELLIDOS[(index + 7) % len(APELLIDOS)]
    return first_name, f"{last_a} {last_b}"


def _phone(index: int) -> str:
    prefix = ("6", "7", "9")[index % 3]
    return f"{prefix}{10_000_000 + index:08d}"


def _dni(index: int, *, base: int) -> str:
    number = base + index
    return f"{number:08d}{_LETRAS_DNI[number % len(_LETRAS_DNI)]}"


def _slug(value: str) -> str:
    return value.lower().replace(" ", "-")


def _build_email(first_name: str, last_name: str, index: int, domains: tuple[str, ...]) -> str:
    primary_last_name = last_name.split()[0]
    domain = domains[index % len(domains)]
    return f"{_slug(first_name)}.{_slug(primary_last_name)}{index % 17}@{domain}"


def _build_address(index: int, rng: random.Random) -> str:
    street = VIAS[(index + rng.randrange(len(VIAS))) % len(VIAS)]
    city = MUNICIPIOS[(index * 3 + rng.randrange(len(MUNICIPIOS))) % len(MUNICIPIOS)]
    portal = 4 + ((index * 7) % 67)
    return f"{street} {portal}, {city}"


def _pick_optional(options: tuple[str, ...], rng: random.Random, *, threshold: float) -> str | None:
    if rng.random() > threshold:
        return None
    return options[rng.randrange(len(options))]


def _pick_patient_index(total: int, rng: random.Random) -> int:
    if total <= 1:
        return 0
    if rng.random() < 0.18:
        return rng.randrange(total)
    return min(total - 1, int((rng.random() ** 2.1) * total))


def _pick_doctor_index(total: int, patient_index: int, rng: random.Random) -> int:
    if total <= 1:
        return 0
    return (patient_index + rng.randrange(total)) % total


def _pick_reason(specialty: str, rng: random.Random) -> str:
    for item in ESPECIALIDADES:
        if item.nombre == specialty:
            return item.motivos[rng.randrange(len(item.motivos))]
    return ESPECIALIDADES[0].motivos[rng.randrange(len(ESPECIALIDADES[0].motivos))]


def _build_notes(reason: str, status: str, rng: random.Random) -> str:
    if rng.random() < 0.22:
        return ""
    fragments = [NOTAS_CITA[rng.randrange(len(NOTAS_CITA))]]
    if status == "NO_PRESENTADO":
        fragments.append("No responde al recordatorio del dia previo.")
    elif status == "CANCELADA":
        fragments.append("Se propone nueva fecha en funcion de disponibilidad.")
    elif "revision" in reason.lower() or "seguimiento" in reason.lower():
        fragments.append("Se valora evolucion y necesidad de nuevo control.")
    return " ".join(fragments)


def _pick_incidence_template(appt: AppointmentCreateDTO, rng: random.Random) -> tuple[str, str, str, str, str]:
    if appt.status == "NO_PRESENTADO":
        return (
            "PACIENTE_NO_LOCALIZADO",
            "WARNING",
            "ABIERTA",
            "No consta confirmacion del paciente en las horas previas a la cita.",
            "Se deja seguimiento manual para revisar el patron de ausencias.",
        )
    if appt.status == "CANCELADA":
        return (
            "REPROGRAMACION_ADMINISTRATIVA",
            "INFO",
            "RESUELTA",
            "La cita se mueve por ajuste administrativo y se ofrece hueco alternativo.",
            "Cambio gestionado por recepcion con confirmacion posterior.",
        )
    return _PLANTILLAS_INCIDENCIA[rng.randrange(len(_PLANTILLAS_INCIDENCIA))]
