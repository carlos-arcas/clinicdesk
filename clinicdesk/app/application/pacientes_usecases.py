from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.domain.repositorios import RepositorioPacientes


@dataclass(frozen=True)
class ListarPacientes:
    """Caso de uso para listar pacientes."""

    repo: RepositorioPacientes

    def ejecutar(self) -> list[Paciente]:
        return self.repo.listar_todos()


@dataclass(frozen=True)
class CrearPaciente:
    """Caso de uso para crear pacientes con validación mínima."""

    repo: RepositorioPacientes

    def ejecutar(self, nombre: str, telefono: str) -> int:
        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip()

        if not nombre:
            raise ValueError("El nombre es obligatorio")

        return self.repo.crear(nombre=nombre, telefono=telefono)
