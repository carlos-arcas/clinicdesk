from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.domain.modelos import Cita
from clinicdesk.app.domain.repositorios import RepositorioCitas, RepositorioPacientes


@dataclass(frozen=True)
class ListarCitas:
    repo: RepositorioCitas

    def ejecutar(self) -> list[Cita]:
        return self.repo.listar_todas()


@dataclass(frozen=True)
class CrearCita:
    """Caso de uso para crear citas con validaciones básicas."""

    repo_citas: RepositorioCitas
    repo_pacientes: RepositorioPacientes

    def ejecutar(self, id_paciente: int, fecha_hora: datetime, motivo: str) -> int:
        motivo = (motivo or "").strip()
        if not motivo:
            raise ValueError("El motivo es obligatorio")

        pacientes = self.repo_pacientes.listar_todos()
        if not any(p.id == id_paciente for p in pacientes):
            raise ValueError("El paciente no existe")

        return self.repo_citas.crear(
            id_paciente=id_paciente,
            fecha_hora=fecha_hora,
            motivo=motivo,
        )
