from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


PresetRangoIntent = Literal["HOY", "PERSONALIZADO"]
PestanaCitasIntent = Literal["LISTA", "CALENDARIO"]
AccionIntentCitas = Literal["SELECCIONAR", "ABRIR_DETALLE"]
FiltroCalidadIntent = Literal["SIN_CHECKIN", "SIN_INICIO_FIN", "SIN_SALIDA"]


@dataclass(frozen=True, slots=True)
class CitasNavigationIntentDTO:
    preset_rango: PresetRangoIntent = "HOY"
    cita_id_destino: int = 0
    filtro_calidad: FiltroCalidadIntent | None = None
    estado_cita: str | None = None
    incluir_riesgo: bool | None = None
    rango_desde: datetime | None = None
    rango_hasta: datetime | None = None
    preferir_pestana: PestanaCitasIntent | None = None
    accion: AccionIntentCitas = "SELECCIONAR"
    resaltar: bool = True
    duracion_resaltado_ms: int = 2500


def debe_abrir_detalle(intent: CitasNavigationIntentDTO, found: bool) -> bool:
    return found and intent.accion == "ABRIR_DETALLE"


def es_intent_calidad(intent: CitasNavigationIntentDTO) -> bool:
    return intent.filtro_calidad is not None
