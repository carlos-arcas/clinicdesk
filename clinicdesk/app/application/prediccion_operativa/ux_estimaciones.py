from __future__ import annotations


TIPOS_ESTIMACION_VALIDOS = {"duracion", "espera"}


def mensaje_no_disponible_estimacion(tipo: str) -> str:
    if tipo in TIPOS_ESTIMACION_VALIDOS:
        return "estimaciones.no_disponible"
    return "estimaciones.no_disponible"


def debe_mostrar_aviso_salud_estimacion(toggle_on: bool, salud_estado: str) -> bool:
    if not toggle_on:
        return False
    return salud_estado.upper().strip() in {"AMARILLO", "ROJO"}
