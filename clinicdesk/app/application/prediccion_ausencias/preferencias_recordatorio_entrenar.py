from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

DIAS_SNOOZE_POR_DEFECTO = 7
CLAVE_RECORDATORIO_FECHA_UTC = "prediccion_ausencias/recordatorio_entrenar/fecha_utc"
CLAVE_RECORDATORIO_DIAS_SNOOZE = "prediccion_ausencias/recordatorio_entrenar/dias_snooze"


@dataclass(frozen=True, slots=True)
class PreferenciaRecordatorioEntrenarDTO:
    fecha_recordatorio_utc: date | None
    dias_snooze: int


def calcular_fecha_recordatorio(ahora_utc: date, dias: int) -> date:
    return ahora_utc + timedelta(days=normalizar_dias_snooze(dias))


def debe_mostrar_recordatorio(ahora_utc: date, salud_estado: str, fecha_recordatorio_utc: date | None) -> bool:
    if salud_estado == "VERDE":
        return False
    if fecha_recordatorio_utc is None:
        return True
    return ahora_utc >= fecha_recordatorio_utc


def normalizar_dias_snooze(valor: Any) -> int:
    try:
        dias = int(valor)
    except (TypeError, ValueError):
        return DIAS_SNOOZE_POR_DEFECTO
    return dias if dias > 0 else DIAS_SNOOZE_POR_DEFECTO


def serializar_fecha_recordatorio_iso(fecha_recordatorio_utc: date | None) -> str:
    return "" if fecha_recordatorio_utc is None else fecha_recordatorio_utc.isoformat()


def deserializar_fecha_recordatorio_iso(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None

