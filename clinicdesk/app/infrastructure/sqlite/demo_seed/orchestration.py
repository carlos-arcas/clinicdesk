from __future__ import annotations

from dataclasses import dataclass
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
from clinicdesk.app.infrastructure.sqlite.demo_seed.contexto_agenda_ml import enriquecer_citas_agenda_ml
from clinicdesk.app.infrastructure.sqlite.demo_seed.operational_history import seed_historial_operativo


@dataclass(slots=True, frozen=True)
class ConfigSeedClinico:
    n_medicamentos: int
    n_materiales: int
    n_recetas: int
    n_movimientos: int
    turns_months: int
    n_ausencias: int
    seed: int
    from_date: date
    to_date: date


@dataclass(slots=True, frozen=True)
class ConteosSeedClinico:
    medicamentos: int
    materiales: int
    recetas: int
    receta_lineas: int
    dispensaciones: int
    movimientos_medicamentos: int
    movimientos_materiales: int
    turnos: int
    ausencias: int


@dataclass(slots=True, frozen=True)
class ResultadoAgendaPersistida:
    doctor_ids: list[int]
    patient_ids: list[int]
    staff_ids: list[int]
    appointment_id_map: dict[str, int]
    incidences_count: int


class SeederProtocol(Protocol):
    _connection: object

    def _normalize_persist_params(
        self, batch_size: int, from_date: date | None, to_date: date | None
    ) -> tuple[int, date, date]: ...

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
    ) -> object: ...


def _seed_clinical_assets(
    seeder: SeederProtocol,
    patient_ids: list[int],
    doctor_ids: list[int],
    staff_ids: list[int],
    *,
    config: ConfigSeedClinico,
) -> ConteosSeedClinico:
    meds_count, mat_count = seed_inventory(seeder._connection, config.n_medicamentos, config.n_materiales)
    recipes_count, line_count, disp_count = seed_recetas_dispensaciones(
        seeder._connection,
        patient_ids,
        doctor_ids,
        staff_ids,
        config.n_recetas,
        config.seed,
        config.from_date,
        config.to_date,
    )
    mov_med, mov_mat = seed_movimientos(
        seeder._connection,
        config.n_movimientos,
        staff_ids,
        config.seed,
        recipes_count > 0,
    )
    turnos_count = seed_turnos_y_calendario(seeder._connection, doctor_ids, staff_ids, config.turns_months)
    ausencias_count = seed_ausencias(seeder._connection, doctor_ids, staff_ids, config.n_ausencias, config.seed)
    return ConteosSeedClinico(
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


def _persist_people_and_agenda(
    seeder: SeederProtocol,
    doctors: list[DoctorCreateDTO],
    patients: list[PatientCreateDTO],
    staff: list[PersonalCreateDTO],
    appointments: list[AppointmentCreateDTO],
    incidences_by_appointment: dict[str, list[IncidenceDTO]],
    *,
    batch_size: int,
) -> ResultadoAgendaPersistida:
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
    return ResultadoAgendaPersistida(
        doctor_ids=doctor_ids,
        patient_ids=patient_ids,
        staff_ids=staff_ids,
        appointment_id_map=appointment_id_map,
        incidences_count=incidences_count,
    )


def _build_persist_result(
    seeder: SeederProtocol,
    agenda: ResultadoAgendaPersistida,
    conteos_seed: ConteosSeedClinico,
):
    return seeder._build_result(
        doctor_ids=agenda.doctor_ids,
        patient_ids=agenda.patient_ids,
        staff_ids=agenda.staff_ids,
        appointment_id_map=agenda.appointment_id_map,
        incidences_count=agenda.incidences_count,
        meds_count=conteos_seed.medicamentos,
        mat_count=conteos_seed.materiales,
        recipes_count=conteos_seed.recetas,
        line_count=conteos_seed.receta_lineas,
        disp_count=conteos_seed.dispensaciones,
        mov_med=conteos_seed.movimientos_medicamentos,
        mov_mat=conteos_seed.movimientos_materiales,
        turnos_count=conteos_seed.turnos,
        ausencias_count=conteos_seed.ausencias,
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
    safe_batch_size, normalized_from_date, normalized_to_date = seeder._normalize_persist_params(
        batch_size,
        from_date,
        to_date,
    )
    agenda = _persist_people_and_agenda(
        seeder,
        doctors,
        patients,
        staff,
        appointments,
        incidences_by_appointment,
        batch_size=safe_batch_size,
    )
    contextos = enriquecer_citas_agenda_ml(seeder._connection, seed=seed, batch_size=safe_batch_size)
    seed_historial_operativo(seeder._connection, contextos, batch_size=safe_batch_size)
    config_seed = ConfigSeedClinico(
        n_medicamentos=n_medicamentos,
        n_materiales=n_materiales,
        n_recetas=n_recetas,
        n_movimientos=n_movimientos,
        turns_months=turns_months,
        n_ausencias=n_ausencias,
        seed=seed,
        from_date=normalized_from_date,
        to_date=normalized_to_date,
    )
    conteos_seed = _seed_clinical_assets(
        seeder,
        agenda.patient_ids,
        agenda.doctor_ids,
        agenda.staff_ids,
        config=config_seed,
    )
    return _build_persist_result(seeder, agenda, conteos_seed)
