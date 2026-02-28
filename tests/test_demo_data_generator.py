from __future__ import annotations

from clinicdesk.app.application.demo_data.generator import (
    AppointmentGenerationConfig,
    generate_appointments,
    generate_doctors,
    generate_incidences,
    generate_patients,
)


def test_generator_is_deterministic() -> None:
    doctors_a = generate_doctors(6, 123)
    doctors_b = generate_doctors(6, 123)
    patients_a = generate_patients(10, 123)
    patients_b = generate_patients(10, 123)
    assert doctors_a == doctors_b
    assert patients_a == patients_b


def test_appointments_reference_existing_doctors_and_patients() -> None:
    doctors = generate_doctors(3, 77)
    patients = generate_patients(7, 77)
    cfg = AppointmentGenerationConfig(n_appointments=120, from_date=_d("2026-01-01"), to_date=_d("2026-02-28"))
    appointments = generate_appointments(patients, doctors, cfg, 77)
    assert len(appointments) == 120
    assert all(0 <= appt.doctor_index < len(doctors) for appt in appointments)
    assert all(0 <= appt.patient_index < len(patients) for appt in appointments)


def test_appointments_distribution_has_weekdays_and_outliers() -> None:
    doctors = generate_doctors(4, 20)
    patients = generate_patients(8, 20)
    cfg = AppointmentGenerationConfig(
        n_appointments=200,
        from_date=_d("2026-01-01"),
        to_date=_d("2026-02-28"),
        weekend_ratio=0.10,
        outlier_ratio=0.04,
    )
    appointments = generate_appointments(patients, doctors, cfg, 20)
    weekday_count = sum(1 for appt in appointments if appt.starts_at.weekday() < 5)
    outliers = sum(1 for appt in appointments if (appt.ends_at - appt.starts_at).total_seconds() / 60 > 60)
    assert weekday_count / len(appointments) >= 0.85
    assert outliers / len(appointments) >= 0.01


def test_incidence_rate_is_approximate() -> None:
    doctors = generate_doctors(5, 45)
    patients = generate_patients(20, 45)
    cfg = AppointmentGenerationConfig(n_appointments=400, from_date=_d("2026-01-01"), to_date=_d("2026-02-28"))
    appointments = generate_appointments(patients, doctors, cfg, 45)
    incidence_map = generate_incidences(appointments, rate=0.2, seed=45)
    total_incidences = sum(len(items) for items in incidence_map.values())
    observed_rate = total_incidences / len(appointments)
    assert 0.14 <= observed_rate <= 0.26


def _d(raw: str):
    from datetime import date

    return date.fromisoformat(raw)
