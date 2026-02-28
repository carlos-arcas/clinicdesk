"""Entidades de dominio relacionadas con citas e incidencias."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from clinicdesk.app.domain.enums import (
    EstadoCita,
    EstadoIncidencia,
    SeveridadIncidencia,
    TipoIncidencia,
    TipoSala,
)
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.value_objects import (
    _ensure_positive_id,
    _require_non_empty,
    _require_override_note,
    _strip_or_none,
)


@dataclass(slots=True)
class Sala:
    """Sala de la clínica (tabla SQL: salas)."""

    id: Optional[int] = None
    nombre: str = ""
    tipo: TipoSala = TipoSala.CONSULTA
    ubicacion: Optional[str] = None
    activa: bool = True

    def validar(self) -> None:
        self.nombre = _require_non_empty(self.nombre, "nombre")
        self.ubicacion = _strip_or_none(self.ubicacion)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tipo"] = self.tipo.value
        return data


@dataclass(slots=True)
class Cita:
    id: Optional[int] = None
    paciente_id: int = 0
    medico_id: int = 0
    sala_id: int = 0
    inicio: datetime = field(default_factory=datetime.now)
    fin: datetime = field(default_factory=datetime.now)
    estado: EstadoCita = EstadoCita.PROGRAMADA
    motivo: Optional[str] = None
    notas: Optional[str] = None
    override_ok: bool = False
    override_nota: Optional[str] = None
    override_personal_id: Optional[int] = None
    override_fecha_hora: Optional[datetime] = None

    def validar(self) -> None:
        _ensure_positive_id(self.paciente_id, "paciente_id")
        _ensure_positive_id(self.medico_id, "medico_id")
        _ensure_positive_id(self.sala_id, "sala_id")

        if self.fin <= self.inicio:
            raise ValidationError("fin debe ser posterior a inicio.")

        self.motivo = _strip_or_none(self.motivo)
        self.notas = _strip_or_none(self.notas)
        self.override_nota = _strip_or_none(self.override_nota)

        if self.override_ok:
            self.override_nota = _require_override_note(self.override_nota)
            if self.override_personal_id is None:
                raise ValidationError("override_personal_id obligatorio para guardar con incidencia.")
            _ensure_positive_id(self.override_personal_id, "override_personal_id")
            if self.override_fecha_hora is None:
                raise ValidationError("override_fecha_hora obligatorio para guardar con incidencia.")

    def duracion_minutos(self) -> int:
        return int((self.fin - self.inicio).total_seconds() // 60)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["inicio"] = self.inicio.isoformat(sep=" ", timespec="seconds")
        data["fin"] = self.fin.isoformat(sep=" ", timespec="seconds")
        data["estado"] = self.estado.value
        if self.override_fecha_hora is not None:
            data["override_fecha_hora"] = self.override_fecha_hora.isoformat(sep=" ", timespec="seconds")
        return data


@dataclass(slots=True)
class Incidencia:
    id: Optional[int] = None
    tipo: TipoIncidencia = TipoIncidencia.CITA_SIN_CUADRANTE
    severidad: SeveridadIncidencia = SeveridadIncidencia.WARNING
    estado: EstadoIncidencia = EstadoIncidencia.ABIERTA
    fecha_hora: datetime = field(default_factory=datetime.now)
    descripcion: str = ""
    medico_id: Optional[int] = None
    personal_id: Optional[int] = None
    cita_id: Optional[int] = None
    dispensacion_id: Optional[int] = None
    receta_id: Optional[int] = None
    confirmado_por_personal_id: int = 0
    nota_override: str = ""

    def validar(self) -> None:
        self.descripcion = _require_non_empty(self.descripcion, "descripcion")
        self.nota_override = _require_non_empty(self.nota_override, "nota_override")
        _ensure_positive_id(self.confirmado_por_personal_id, "confirmado_por_personal_id")

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tipo"] = self.tipo.value
        data["severidad"] = self.severidad.value
        data["estado"] = self.estado.value
        data["fecha_hora"] = self.fecha_hora.isoformat(sep=" ", timespec="seconds")
        return data
