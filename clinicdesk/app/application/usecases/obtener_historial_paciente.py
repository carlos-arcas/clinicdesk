from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.queries.historial_paciente_queries import CitaHistorialRow
from clinicdesk.app.queries.recetas_queries import RecetaRow


class PacienteDetalleGateway(Protocol):
    def get_by_id(self, paciente_id: int) -> Paciente | None:
        ...


class HistorialCitasGateway(Protocol):
    def listar_citas_por_paciente(self, paciente_id: int, *, limite: int = 200) -> list[CitaHistorialRow]:
        ...


class HistorialRecetasGateway(Protocol):
    def list_por_paciente(self, paciente_id: int) -> list[RecetaRow]:
        ...


@dataclass(frozen=True, slots=True)
class HistorialPacienteResultado:
    paciente_detalle: Paciente
    citas: tuple[CitaHistorialRow, ...]
    recetas: tuple[RecetaRow, ...]


class ObtenerHistorialPaciente:
    def __init__(
        self,
        pacientes_gateway: PacienteDetalleGateway,
        citas_gateway: HistorialCitasGateway,
        recetas_gateway: HistorialRecetasGateway,
    ) -> None:
        self._pacientes_gateway = pacientes_gateway
        self._citas_gateway = citas_gateway
        self._recetas_gateway = recetas_gateway

    def execute(self, paciente_id: int) -> HistorialPacienteResultado | None:
        paciente = self._pacientes_gateway.get_by_id(paciente_id)
        if paciente is None:
            return None
        citas = self._citas_gateway.listar_citas_por_paciente(paciente_id)
        recetas = self._recetas_gateway.list_por_paciente(paciente_id)
        return HistorialPacienteResultado(
            paciente_detalle=paciente,
            citas=tuple(citas),
            recetas=tuple(recetas),
        )
