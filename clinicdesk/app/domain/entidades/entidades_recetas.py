"""Entidades de dominio para recetas y dispensaciones."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.value_objects import (
    _ensure_non_negative,
    _ensure_positive_id,
    _require_non_empty,
    _require_override_note,
    _strip_or_none,
)


@dataclass(slots=True)
class Receta:
    id: Optional[int] = None
    paciente_id: int = 0
    medico_id: int = 0
    fecha: datetime = field(default_factory=datetime.now)
    observaciones: Optional[str] = None

    def validar(self) -> None:
        _ensure_positive_id(self.paciente_id, "paciente_id")
        _ensure_positive_id(self.medico_id, "medico_id")
        self.observaciones = _strip_or_none(self.observaciones)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["fecha"] = self.fecha.isoformat(sep=" ", timespec="seconds")
        return data


@dataclass(slots=True)
class RecetaLinea:
    id: Optional[int] = None
    receta_id: int = 0
    medicamento_id: int = 0
    dosis: str = ""
    duracion_dias: Optional[int] = None
    instrucciones: Optional[str] = None

    def validar(self) -> None:
        _ensure_positive_id(self.receta_id, "receta_id")
        _ensure_positive_id(self.medicamento_id, "medicamento_id")
        self.dosis = _require_non_empty(self.dosis, "dosis")
        if self.duracion_dias is not None and self.duracion_dias <= 0:
            raise ValidationError("duracion_dias debe ser > 0 si se indica.")
        self.instrucciones = _strip_or_none(self.instrucciones)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Dispensacion:
    id: Optional[int] = None
    receta_id: int = 0
    receta_linea_id: Optional[int] = None
    medicamento_id: int = 0
    personal_id: int = 0
    fecha_hora: datetime = field(default_factory=datetime.now)
    cantidad: int = 0
    observaciones: Optional[str] = None
    override_ok: bool = False
    override_nota: Optional[str] = None
    override_personal_id: Optional[int] = None
    override_fecha_hora: Optional[datetime] = None

    def validar(self) -> None:
        _ensure_positive_id(self.receta_id, "receta_id")
        _ensure_positive_id(self.medicamento_id, "medicamento_id")
        _ensure_positive_id(self.personal_id, "personal_id")
        _ensure_non_negative(self.cantidad, "cantidad")
        self.observaciones = _strip_or_none(self.observaciones)
        self.override_nota = _strip_or_none(self.override_nota)
        if self.override_ok:
            self.override_nota = _require_override_note(self.override_nota)
            if self.override_personal_id is None:
                raise ValidationError("override_personal_id obligatorio para guardar con incidencia.")
            _ensure_positive_id(self.override_personal_id, "override_personal_id")
            if self.override_fecha_hora is None:
                raise ValidationError("override_fecha_hora obligatorio para guardar con incidencia.")

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["fecha_hora"] = self.fecha_hora.isoformat(sep=" ", timespec="seconds")
        if self.override_fecha_hora is not None:
            data["override_fecha_hora"] = self.override_fecha_hora.isoformat(sep=" ", timespec="seconds")
        return data


__all__ = ["Receta", "RecetaLinea", "Dispensacion"]
