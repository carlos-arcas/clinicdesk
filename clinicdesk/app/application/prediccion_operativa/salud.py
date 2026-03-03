from __future__ import annotations

from datetime import datetime, timezone


_MAX_VERDE_DIAS = 14
_MAX_AMARILLO_DIAS = 45


def resolver_estado_salud(fecha_entrenamiento: str | None, citas_validas_recientes: int) -> str:
    dias = _dias_desde_entrenamiento(fecha_entrenamiento)
    if dias is None:
        return "ROJO"
    if _es_verde(dias, citas_validas_recientes):
        return "VERDE"
    if _es_amarillo(dias, citas_validas_recientes):
        return "AMARILLO"
    return "ROJO"


def _dias_desde_entrenamiento(fecha_entrenamiento: str | None) -> int | None:
    if not fecha_entrenamiento:
        return None
    try:
        fecha = datetime.fromisoformat(fecha_entrenamiento)
    except ValueError:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - fecha).days)


def _es_verde(dias: int, citas_validas_recientes: int) -> bool:
    return dias <= _MAX_VERDE_DIAS and citas_validas_recientes >= 50


def _es_amarillo(dias: int, citas_validas_recientes: int) -> bool:
    return dias <= _MAX_AMARILLO_DIAS and citas_validas_recientes >= 20
