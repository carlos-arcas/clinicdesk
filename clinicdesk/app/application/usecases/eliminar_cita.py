from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.security import UserContext
from clinicdesk.app.domain.repositorios import RepositorioCitas


@dataclass(frozen=True)
class EliminarCitaUseCase:
    repo: RepositorioCitas
    user_context: UserContext

    def execute(self, cita_id: int) -> None:
        if cita_id <= 0:
            raise ValueError("cita_id inválido")
        self.user_context.require_write("citas.eliminar")
        self.repo.delete(cita_id)

