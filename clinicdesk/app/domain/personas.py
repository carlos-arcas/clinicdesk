"""Entidades de dominio relacionadas con personas."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Dict, Optional

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.value_objects import (
    _require_non_empty,
    _strip_or_none,
    _validate_email_basic,
    _validate_phone_basic,
)


@dataclass(slots=True)
class Persona:
    """Clase base para personas del dominio (no tiene tabla SQL propia)."""

    id: Optional[int] = None
    tipo_documento: TipoDocumento = TipoDocumento.DNI
    documento: str = ""
    nombre: str = ""
    apellidos: str = ""
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    direccion: Optional[str] = None
    activo: bool = True

    def validar(self) -> None:
        """Invariantes comunes para cualquier persona."""
        self.documento = _require_non_empty(self.documento, "documento")
        self.nombre = _require_non_empty(self.nombre, "nombre")
        self.apellidos = _require_non_empty(self.apellidos, "apellidos")

        self.telefono = _strip_or_none(self.telefono)
        self.email = _strip_or_none(self.email)
        self.direccion = _strip_or_none(self.direccion)

        _validate_phone_basic(self.telefono)
        _validate_email_basic(self.email)

    def nombre_completo(self) -> str:
        """Nombre completo para listados o documentos."""
        return f"{self.nombre} {self.apellidos}".strip()

    def to_dict(self) -> Dict[str, Any]:
        """Serialización básica a dict (útil para CSV/JSON)."""
        data = asdict(self)
        data["tipo_documento"] = self.tipo_documento.value
        if self.fecha_nacimiento is not None:
            data["fecha_nacimiento"] = self.fecha_nacimiento.isoformat()
        return data


@dataclass(slots=True)
class Paciente(Persona):
    """Paciente (tabla SQL: pacientes)."""

    num_historia: Optional[str] = None
    alergias: Optional[str] = None
    observaciones: Optional[str] = None

    def validar(self) -> None:
        super(Paciente, self).validar()
        self.num_historia = _strip_or_none(self.num_historia)
        self.alergias = _strip_or_none(self.alergias)
        self.observaciones = _strip_or_none(self.observaciones)


@dataclass(slots=True)
class Medico(Persona):
    """Médico (tabla SQL: medicos)."""

    num_colegiado: str = ""
    especialidad: str = ""

    def validar(self) -> None:
        super(Medico, self).validar()
        self.num_colegiado = _require_non_empty(self.num_colegiado, "num_colegiado")
        self.especialidad = _require_non_empty(self.especialidad, "especialidad")


@dataclass(slots=True)
class Personal(Persona):
    """Personal (tabla SQL: personal)."""

    puesto: str = ""
    turno: Optional[str] = None

    def validar(self) -> None:
        super(Personal, self).validar()
        self.puesto = _require_non_empty(self.puesto, "puesto")
        self.turno = _strip_or_none(self.turno)
