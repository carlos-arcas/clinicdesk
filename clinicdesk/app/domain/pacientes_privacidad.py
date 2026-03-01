"""Clasificación de sensibilidad para atributos de paciente."""

from __future__ import annotations

from enum import StrEnum


class NivelSensibilidad(StrEnum):
    PUBLICO = "publico"
    PERSONAL = "personal"
    SENSIBLE = "sensible"


NIVEL_SENSIBILIDAD_POR_ATRIBUTO: dict[str, NivelSensibilidad] = {
    "id": NivelSensibilidad.PUBLICO,
    "tipo_documento": NivelSensibilidad.PUBLICO,
    "documento": NivelSensibilidad.PERSONAL,
    "nombre": NivelSensibilidad.PUBLICO,
    "apellidos": NivelSensibilidad.PUBLICO,
    "nombre_completo": NivelSensibilidad.PUBLICO,
    "telefono": NivelSensibilidad.PERSONAL,
    "email": NivelSensibilidad.PERSONAL,
    "fecha_nacimiento": NivelSensibilidad.PERSONAL,
    "direccion": NivelSensibilidad.PERSONAL,
    "activo": NivelSensibilidad.PUBLICO,
    "num_historia": NivelSensibilidad.SENSIBLE,
    "alergias": NivelSensibilidad.SENSIBLE,
    "observaciones": NivelSensibilidad.SENSIBLE,
}


def nivel_sensibilidad_de_atributo(atributo: str) -> NivelSensibilidad:
    """Obtiene la sensibilidad de un atributo; por defecto SENSIBLE."""
    return NIVEL_SENSIBILIDAD_POR_ATRIBUTO.get(atributo, NivelSensibilidad.SENSIBLE)
