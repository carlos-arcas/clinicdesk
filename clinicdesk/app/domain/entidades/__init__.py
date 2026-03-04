"""Paquete de entidades de dominio agrupadas por cohesión."""

from clinicdesk.app.domain.entidades.entidades_farmacia_stock import (
    Material,
    Medicamento,
    MovimientoMaterial,
    MovimientoMedicamento,
)
from clinicdesk.app.domain.entidades.entidades_recetas import (
    Dispensacion,
    Receta,
    RecetaLinea,
)

__all__ = [
    "Medicamento",
    "Material",
    "MovimientoMedicamento",
    "MovimientoMaterial",
    "Receta",
    "RecetaLinea",
    "Dispensacion",
]
