"""Clasificación de sensibilidad para atributos de citas."""

from __future__ import annotations

from enum import StrEnum


class NivelSensibilidadCita(StrEnum):
    PUBLICO = "publico"
    PERSONAL = "personal"
    SENSIBLE = "sensible"


NIVEL_SENSIBILIDAD_POR_ATRIBUTO_CITA: dict[str, NivelSensibilidadCita] = {
    "id": NivelSensibilidadCita.PUBLICO,
    "fecha": NivelSensibilidadCita.PUBLICO,
    "hora_inicio": NivelSensibilidadCita.PUBLICO,
    "hora_fin": NivelSensibilidadCita.PUBLICO,
    "paciente": NivelSensibilidadCita.PUBLICO,
    "medico": NivelSensibilidadCita.PUBLICO,
    "sala": NivelSensibilidadCita.PUBLICO,
    "estado": NivelSensibilidadCita.PUBLICO,
    "notas": NivelSensibilidadCita.SENSIBLE,
    "notas_len": NivelSensibilidadCita.SENSIBLE,
    "motivo": NivelSensibilidadCita.PERSONAL,
}


def nivel_sensibilidad_atributo_cita(atributo: str) -> NivelSensibilidadCita:
    """Obtiene la sensibilidad de un atributo de cita; por defecto SENSIBLE."""
    return NIVEL_SENSIBILIDAD_POR_ATRIBUTO_CITA.get(atributo, NivelSensibilidadCita.SENSIBLE)
