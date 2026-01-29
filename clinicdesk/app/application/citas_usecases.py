from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from clinicdesk.app.domain.modelos import Cita
from clinicdesk.app.domain.repositorios import RepositorioCitas, RepositorioPacientes
# Importamos contratos para mantener la app desacoplada de SQLite.


@dataclass(frozen=True)
class ListarCitas:
    repo: RepositorioCitas

    def ejecutar(self) -> List[Cita]:
        return self.repo.listar_todas()


@dataclass(frozen=True)
class CrearCita:
    """
    Caso de uso: crear cita.
    Ejemplo de regla básica: que exista el paciente.
    (Más reglas posibles: no en pasado, motivo obligatorio, etc.)
    """
    repo_citas: RepositorioCitas
    repo_pacientes: RepositorioPacientes

    def ejecutar(self, id_paciente: int, fecha_hora: datetime, motivo: str) -> int:
        motivo = (motivo or "").strip()
        if not motivo:
            raise ValueError("El motivo es obligatorio")

        # Regla: el paciente debe existir.
        pacientes = self.repo_pacientes.listar_todos()
        if not any(p.id == id_paciente for p in pacientes):
            raise ValueError("El paciente no existe")

        return self.repo_citas.crear(id_paciente=id_paciente, fecha_hora=fecha_hora, motivo=motivo)
