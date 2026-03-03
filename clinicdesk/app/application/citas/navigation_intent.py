from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PresetRangoIntent = Literal["HOY"]
PestanaCitasIntent = Literal["LISTA", "CALENDARIO"]


@dataclass(frozen=True, slots=True)
class CitasNavigationIntentDTO:
    preset_rango: PresetRangoIntent
    cita_id_destino: int
    preferir_pestana: PestanaCitasIntent | None = None

