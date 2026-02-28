from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.security import UserContext
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.domain.repositorios import RepositorioPacientes


@dataclass(frozen=True)
class CrearPacienteUseCase:
    repo: RepositorioPacientes
    user_context: UserContext

    def execute(self, paciente: Paciente) -> int:
        self.user_context.require_write("pacientes.crear")
        return self.repo.create(paciente)


@dataclass(frozen=True)
class EditarPacienteUseCase:
    repo: RepositorioPacientes
    user_context: UserContext

    def execute(self, paciente: Paciente) -> None:
        self.user_context.require_write("pacientes.editar")
        self.repo.update(paciente)


@dataclass(frozen=True)
class DesactivarPacienteUseCase:
    repo: RepositorioPacientes
    user_context: UserContext

    def execute(self, paciente_id: int) -> None:
        self.user_context.require_write("pacientes.desactivar")
        self.repo.delete(paciente_id)
