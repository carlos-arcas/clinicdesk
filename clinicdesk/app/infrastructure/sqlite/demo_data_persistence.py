from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from clinicdesk.app.application.demo_data.dtos import AppointmentCreateDTO, IncidenceDTO
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


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
