"""Inventario canónico de atributos de paciente."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TipoAtributo = Literal["str", "int", "date", "bool", "optional"]


@dataclass(frozen=True, slots=True)
class AtributoPaciente:
    """Describe un atributo de paciente para contratos de aplicación."""

    nombre: str
    tipo: TipoAtributo
    fuentes: tuple[str, ...]


ATRIBUTOS_PACIENTE: tuple[AtributoPaciente, ...] = (
    AtributoPaciente("id", "int", ("dominio", "tabla sqlite", "DTO")),
    AtributoPaciente("tipo_documento", "str", ("dominio", "tabla sqlite")),
    AtributoPaciente("documento", "str", ("dominio", "tabla sqlite", "DTO")),
    AtributoPaciente("nombre", "str", ("dominio", "tabla sqlite")),
    AtributoPaciente("apellidos", "str", ("dominio", "tabla sqlite")),
    AtributoPaciente("nombre_completo", "str", ("DTO",)),
    AtributoPaciente("telefono", "optional", ("dominio", "tabla sqlite", "DTO")),
    AtributoPaciente("email", "optional", ("dominio", "tabla sqlite")),
    AtributoPaciente("fecha_nacimiento", "optional", ("dominio", "tabla sqlite")),
    AtributoPaciente("direccion", "optional", ("dominio", "tabla sqlite")),
    AtributoPaciente("activo", "bool", ("dominio", "tabla sqlite", "DTO")),
    AtributoPaciente("num_historia", "optional", ("dominio", "tabla sqlite")),
    AtributoPaciente("alergias", "optional", ("dominio", "tabla sqlite")),
    AtributoPaciente("observaciones", "optional", ("dominio", "tabla sqlite")),
)


def nombres_atributos_paciente() -> tuple[str, ...]:
    """Devuelve nombres de atributos en orden estable."""
    return tuple(atributo.nombre for atributo in ATRIBUTOS_PACIENTE)
