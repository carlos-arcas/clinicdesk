from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class CitaReadModel:
    """Vista de lectura mínima para extracción de dataset de citas."""

    cita_id: str
    paciente_id: int
    medico_id: int
    inicio: datetime
    fin: datetime
    estado: str
    notas: str | None = None
    has_incidencias: bool = False


class CitasReadPort(Protocol):
    """Puerto de lectura para extracción reproducible de citas."""

    def list_in_range(self, desde: datetime, hasta: datetime) -> list[CitaReadModel]:
        """Devuelve citas cuyo inicio cae dentro del rango solicitado."""
