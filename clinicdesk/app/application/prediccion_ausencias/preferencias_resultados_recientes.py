from __future__ import annotations

from typing import Any

VENTANAS_RESULTADOS_PERMITIDAS = (4, 8, 12)
VENTANA_RESULTADOS_POR_DEFECTO = 8
CLAVE_VENTANA_RESULTADOS_RECIENTES = "prediccion_ausencias/resultados_recientes/ventana_semanas"


def normalizar_ventana_resultados_semanas(valor: Any) -> int:
    try:
        semanas = int(valor)
    except (TypeError, ValueError):
        return VENTANA_RESULTADOS_POR_DEFECTO
    return semanas if semanas in VENTANAS_RESULTADOS_PERMITIDAS else VENTANA_RESULTADOS_POR_DEFECTO


def serializar_ventana_resultados_semanas(semanas: int) -> str:
    return str(normalizar_ventana_resultados_semanas(semanas))


def deserializar_ventana_resultados_semanas(valor: Any) -> int:
    return normalizar_ventana_resultados_semanas(valor)
