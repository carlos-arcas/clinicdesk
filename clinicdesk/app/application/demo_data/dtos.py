from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class DoctorCreateDTO:
    document_type: str
    document: str
    first_name: str
    last_name: str
    phone: str
    email: str
    birth_date: date
    address: str
    collegiate_number: str
    specialty: str


@dataclass(slots=True)
class PatientCreateDTO:
    document_type: str
    document: str
    first_name: str
    last_name: str
    phone: str
    email: str
    birth_date: date
    address: str
    allergies: str | None
    observations: str | None


@dataclass(slots=True)
class PersonalCreateDTO:
    document_type: str
    document: str
    first_name: str
    last_name: str
    phone: str
    email: str
    birth_date: date
    address: str
    role: str
    shift: str


@dataclass(slots=True)
class AppointmentCreateDTO:
    external_id: str
    patient_index: int
    doctor_index: int
    starts_at: datetime
    ends_at: datetime
    status: str
    reason: str
    notes: str


@dataclass(slots=True)
class IncidenceDTO:
    appointment_external_id: str
    incidence_type: str
    severity: str
    status: str
    occurred_at: datetime
    description: str
    override_note: str
