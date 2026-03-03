from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PresetRangoIntent = Literal["HOY"]
PestanaCitasIntent = Literal["LISTA", "CALENDARIO"]
AccionIntentCitas = Literal["SELECCIONAR", "ABRIR_DETALLE"]


@dataclass(frozen=True, slots=True)
class CitasNavigationIntentDTO:
    preset_rango: PresetRangoIntent
    cita_id_destino: int
    preferir_pestana: PestanaCitasIntent | None = None
    accion: AccionIntentCitas = "SELECCIONAR"
    resaltar: bool = True
    duracion_resaltado_ms: int = 2500


def debe_abrir_detalle(intent: CitasNavigationIntentDTO, found: bool) -> bool:
    return found and intent.accion == "ABRIR_DETALLE"
