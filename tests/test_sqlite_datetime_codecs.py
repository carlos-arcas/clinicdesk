from __future__ import annotations

import warnings
from datetime import datetime, timedelta

from clinicdesk.app.application.demo_data.dtos import AppointmentCreateDTO
from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.modelos import Cita
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import persist_appointments_rows
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository


def test_citas_roundtrip_datetime_preserva_valor(container, seed_data) -> None:
    inicio = datetime(2026, 3, 5, 9, 15, 33, 321000)
    fin = inicio + timedelta(minutes=45)
    cita = Cita(
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio=inicio,
        fin=fin,
        estado=EstadoCita.PROGRAMADA,
        motivo="Control",
        notas="Roundtrip datetime",
    )
    repo = CitasRepository(container.connection)

    cita_id = repo.create(cita)
    guardada = repo.get_by_id(cita_id)

    assert guardada is not None
    assert guardada.inicio == inicio
    assert guardada.fin == fin


def test_persist_citas_no_emite_deprecation_warning_datetime(db_connection, seed_data) -> None:
    appointment = AppointmentCreateDTO(
        external_id="appt-1",
        patient_index=0,
        doctor_index=0,
        starts_at=datetime(2026, 4, 1, 8, 0, 0),
        ends_at=datetime(2026, 4, 1, 8, 30, 0),
        status=EstadoCita.PROGRAMADA.value,
        reason="Control sin warning",
        notes="",
    )

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        persist_appointments_rows(
            db_connection,
            [appointment],
            [seed_data["paciente_activo_id"]],
            [seed_data["medico_activo_id"]],
            [seed_data["sala_activa_id"]],
            batch_size=1,
        )

    sqlite_warnings = [
        warning
        for warning in captured
        if "default datetime adapter is deprecated" in str(warning.message)
    ]
    assert sqlite_warnings == []
