from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class EventoTelemetriaDTO:
    timestamp_utc: str
    usuario: str
    modo_demo: bool
    evento: str
    contexto: str | None = None
    entidad_tipo: str | None = None
    entidad_id: str | None = None


def ahora_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
