from __future__ import annotations

from dataclasses import dataclass
from typing import List

from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.domain.repositorios import RepositorioPacientes
# Importamos el contrato (RepositorioPacientes) para depender de abstracciones, no de SQLite.


@dataclass(frozen=True)
class ListarPacientes:
    """
    Caso de uso: listar pacientes.
    La UI llama a ejecutar() y recibe List[Paciente].
    """
    repo: RepositorioPacientes

    def ejecutar(self) -> List[Paciente]:
        return self.repo.listar_todos()


@dataclass(frozen=True)
class CrearPaciente:
    """
    Caso de uso: crear paciente con validación mínima.
    Aquí vive la regla: nombre obligatorio.
    """
    repo: RepositorioPacientes

    def ejecutar(self, nombre: str, telefono: str) -> int:
        nombre = (nombre or "").strip()
        telefono = (telefono or "").strip()

        if not nombre:
            raise ValueError("El nombre es obligatorio")

        return self.repo.crear(nombre=nombre, telefono=telefono)