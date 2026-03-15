from __future__ import annotations

from datetime import datetime

from clinicdesk.app.application.citas import FiltrosCitasDTO
from clinicdesk.app.pages.citas.logging_payloads import payload_log_error_calendario


def test_payload_log_error_calendario_incluye_reason_code_y_contexto() -> None:
    filtros = FiltrosCitasDTO(
        rango_preset="SEMANA",
        desde=datetime(2026, 1, 1, 0, 0, 0),
        hasta=datetime(2026, 1, 7, 23, 59, 59),
        estado_cita="PROGRAMADA",
        medico_id=11,
        sala_id=3,
        paciente_id=22,
    )

    payload = payload_log_error_calendario(
        filtros,
        fecha_calendario="2026-01-05",
        exc=RuntimeError("boom"),
    )

    assert payload["action"] == "citas_calendario_error"
    assert payload["reason_code"] == "CALENDARIO_REFRESH_EXCEPTION"
    assert payload["contexto"] == "CALENDARIO"
    assert payload["error"] == "RuntimeError"
    assert payload["preset"] == "SEMANA"
    assert payload["fecha_calendario"] == "2026-01-05"
