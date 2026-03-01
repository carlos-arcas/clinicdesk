from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from clinicdesk.app.application.demo_data.dtos import IncidenceDTO
from clinicdesk.app.infrastructure.sqlite.demo_seed.appointments import _iter_batches
from clinicdesk.app.infrastructure.sqlite.demo_seed.types import BatchProgress


def _flatten_incidences(
    incidences_by_appointment: dict[str, list[IncidenceDTO]],
    appointment_ids: dict[str, int],
) -> list[tuple[int, IncidenceDTO]]:
    flattened: list[tuple[int, IncidenceDTO]] = []
    for external_id, entries in incidences_by_appointment.items():
        cita_id = appointment_ids.get(external_id)
        if cita_id is None:
            continue
        flattened.extend((cita_id, entry) for entry in entries)
    return flattened


def _insert_incidence_row(
    connection: sqlite3.Connection,
    cita_id: int,
    entry: IncidenceDTO,
    confirmer_id: int,
) -> None:
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
    flattened = _flatten_incidences(incidences_by_appointment, appointment_ids)
    total_rows = len(flattened)
    if total_rows == 0:
        return 0
    total_batches = (total_rows + batch_size - 1) // batch_size
    tracker = BatchProgress("persist_incidences", total_rows, total_batches, datetime.now(UTC))
    total = 0
    for batch_index, batch in enumerate(_iter_batches(flattened, batch_size), start=1):
        for cita_id, entry in batch:
            confirmer_id = staff_ids[cita_id % len(staff_ids)]
            _insert_incidence_row(connection, cita_id, entry, confirmer_id)
            total += 1
        connection.commit()
        tracker.log_batch(batch_index, total)
    return total
