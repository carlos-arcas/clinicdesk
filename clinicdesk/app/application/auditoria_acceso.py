from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class AccionAuditoriaAcceso(str, Enum):
    VER_HISTORIAL_PACIENTE = "VER_HISTORIAL_PACIENTE"
    VER_DETALLE_CITA = "VER_DETALLE_CITA"
    COPIAR_INFORME_CITA = "COPIAR_INFORME_CITA"
    VER_DETALLE_RECETA = "VER_DETALLE_RECETA"


class EntidadAuditoriaAcceso(str, Enum):
    PACIENTE = "PACIENTE"
    CITA = "CITA"
    RECETA = "RECETA"


@dataclass(frozen=True, slots=True)
class EventoAuditoriaAcceso:
    timestamp_utc: str
    usuario: str
    modo_demo: bool
    accion: AccionAuditoriaAcceso
    entidad_tipo: EntidadAuditoriaAcceso
    entidad_id: str
    metadata_json: dict[str, str | int | float | bool | None] | None = None
    id: int | None = None



def now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()
