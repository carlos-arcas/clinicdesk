"""Entidades de dominio (módulo de compatibilidad)."""

from clinicdesk.app.domain.citas import Cita, Incidencia, Sala
from clinicdesk.app.domain.entidades import (
    Dispensacion,
    Material,
    Medicamento,
    MovimientoMaterial,
    MovimientoMedicamento,
    Receta,
    RecetaLinea,
)
from clinicdesk.app.domain.personas import Medico, Paciente, Persona, Personal

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
