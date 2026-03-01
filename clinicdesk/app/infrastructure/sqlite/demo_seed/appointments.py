from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import TypeVar

from clinicdesk.app.application.demo_data.dtos import AppointmentCreateDTO
from clinicdesk.app.infrastructure.sqlite.demo_seed.types import BatchProgress
from clinicdesk.app.infrastructure.sqlite.sqlite_datetime_codecs import serialize_datetime

T = TypeVar("T")


def _iter_batches(items: list[T], batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


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
    tracker = BatchProgress("persist_appointments", total, total_batches, datetime.now(UTC))
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
                    serialize_datetime(dto.starts_at),
                    serialize_datetime(dto.ends_at),
                    dto.status,
                    dto.reason,
                    dto.notes,
                ),
            )
            appointment_id_map[dto.external_id] = int(cur.lastrowid)
        connection.commit()
        tracker.log_batch(batch_index, len(appointment_id_map))
    return appointment_id_map
