from __future__ import annotations

CLAVES_COLUMNAS_CONFIRMACIONES: tuple[str, ...] = (
    "seleccion",
    "fecha",
    "hora",
    "paciente",
    "medico",
    "estado",
    "riesgo",
    "recordatorio",
    "acciones",
)


def claves_columnas_confirmaciones() -> tuple[str, ...]:
    return CLAVES_COLUMNAS_CONFIRMACIONES

