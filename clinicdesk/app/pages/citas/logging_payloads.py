from __future__ import annotations

from clinicdesk.app.application.citas import FiltrosCitasDTO


def payload_log_error_calendario(
    filtros: FiltrosCitasDTO, *, fecha_calendario: str, exc: Exception
) -> dict[str, object]:
    return {
        "action": "citas_calendario_error",
        "error": exc.__class__.__name__,
        "reason_code": "CALENDARIO_REFRESH_EXCEPTION",
        "contexto": "CALENDARIO",
        "preset": filtros.rango_preset,
        "desde": filtros.desde.isoformat() if filtros.desde else None,
        "hasta": filtros.hasta.isoformat() if filtros.hasta else None,
        "estado": filtros.estado_cita,
        "medico_id": filtros.medico_id,
        "sala_id": filtros.sala_id,
        "paciente_id": filtros.paciente_id,
        "fecha_calendario": fecha_calendario,
    }
