"""Compatibilidad histórica para imports desde `domain.modelos`."""

from clinicdesk.app.domain.entities import (
    Cita,
    Dispensacion,
    Incidencia,
    Material,
    Medico,
    Medicamento,
    MovimientoMaterial,
    MovimientoMedicamento,
    Paciente,
    Persona,
    Personal,
    Receta,
    RecetaLinea,
    Sala,
)

__all__ = [
    "Persona",
    "Paciente",
    "Medico",
    "Personal",
    "Sala",
    "Medicamento",
    "Material",
    "MovimientoMedicamento",
    "MovimientoMaterial",
    "Cita",
    "Receta",
    "RecetaLinea",
    "Dispensacion",
    "Incidencia",
]
