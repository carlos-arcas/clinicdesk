from __future__ import annotations

from datetime import date
from typing import Protocol

from clinicdesk.app.application.demo_data.dtos import (
    AppointmentCreateDTO,
    DoctorCreateDTO,
    IncidenceDTO,
    PatientCreateDTO,
    PersonalCreateDTO,
)
from clinicdesk.app.infrastructure.sqlite.demo_data_seed_helpers import (
    seed_ausencias,
    seed_inventory,
    seed_movimientos,
    seed_recetas_dispensaciones,
    seed_turnos_y_calendario,
)


class SeederProtocol(Protocol):
    _connection: object

    def _normalize_persist_params(self, batch_size: int, from_date: date | None, to_date: date | None) -> tuple[int, date, date]: ...

    def _persist_people(
        self,
        doctors: list[DoctorCreateDTO],
        patients: list[PatientCreateDTO],
        staff: list[PersonalCreateDTO],
    ) -> tuple[list[int], list[int], list[int]]: ...

    def _ensure_salas(self) -> list[int]: ...

    def _persist_appointments(
        self,
        appointments: list[AppointmentCreateDTO],
        patient_ids: list[int],
        doctor_ids: list[int],
        room_ids: list[int],
        *,
        batch_size: int,
    ) -> dict[str, int]: ...

    def _persist_incidences(
        self,
        incidences_by_appointment: dict[str, list[IncidenceDTO]],
        appointment_ids: dict[str, int],
        staff_ids: list[int],
        *,
        batch_size: int,
    ) -> int: ...


def _seed_clinical_assets(
    seeder: SeederProtocol,
    patient_ids: list[int],
    doctor_ids: list[int],
    staff_ids: list[int],
    *,
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




def _persist_people_and_agenda(
    seeder: SeederProtocol,
    doctors: list[DoctorCreateDTO],
    patients: list[PatientCreateDTO],
    staff: list[PersonalCreateDTO],
    appointments: list[AppointmentCreateDTO],
    incidences_by_appointment: dict[str, list[IncidenceDTO]],
    *,
    batch_size: int,
) -> tuple[list[int], list[int], list[int], dict[str, int], int]:
    doctor_ids, patient_ids, staff_ids = seeder._persist_people(doctors, patients, staff)
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
    return doctor_ids, patient_ids, staff_ids, appointment_id_map, incidences_count




def _build_persist_result(
    seeder: SeederProtocol,
    doctor_ids: list[int],
    patient_ids: list[int],
    staff_ids: list[int],
    appointment_id_map: dict[str, int],
    incidences_count: int,
    seed_counts: tuple[int, int, int, int, int, int, int, int, int],
):
    meds_count, mat_count, recipes_count, line_count, disp_count, mov_med, mov_mat, turnos_count, ausencias_count = seed_counts
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

def persist_demo_data(
    *,
    seeder: SeederProtocol,
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
):
    safe_batch_size, from_date, to_date = seeder._normalize_persist_params(batch_size, from_date, to_date)
    doctor_ids, patient_ids, staff_ids, appointment_id_map, incidences_count = _persist_people_and_agenda(
        seeder,
        doctors,
        patients,
        staff,
        appointments,
        incidences_by_appointment,
        batch_size=safe_batch_size,
    )
    seed_counts = _seed_clinical_assets(
        seeder,
        patient_ids,
        doctor_ids,
        staff_ids,
        n_medicamentos=n_medicamentos,
        n_materiales=n_materiales,
        n_recetas=n_recetas,
        n_movimientos=n_movimientos,
        turns_months=turns_months,
        n_ausencias=n_ausencias,
        seed=seed,
        from_date=from_date,
        to_date=to_date,
    )
    return _build_persist_result(
        seeder,
        doctor_ids,
        patient_ids,
        staff_ids,
        appointment_id_map,
        incidences_count,
        seed_counts,
    )
