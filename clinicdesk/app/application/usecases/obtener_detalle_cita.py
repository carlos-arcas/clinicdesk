from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.queries.historial_paciente_queries import DetalleCitaRow, IncidenciaCitaRow


class DetalleCitaGateway(Protocol):
    def obtener_detalle_cita(self, cita_id: int, *, limite_incidencias: int = 3) -> DetalleCitaRow | None:
        ...


class DetalleCitaNoEncontradaError(ValueError):
    def __init__(self) -> None:
        super().__init__("pacientes.historial.citas.detalle.error.no_encontrada")


@dataclass(frozen=True, slots=True)
class IncidenciaDetalleDTO:
    id: int
    fecha_hora: str
    estado: str
    resumen: str


@dataclass(frozen=True, slots=True)
class DetalleCitaDTO:
    id: int
    fecha: str
    hora_inicio: str
    hora_fin: str
    estado: str
    sala: str
    medico: str
    paciente: str
    informe: str
    total_incidencias: int
    incidencias: tuple[IncidenciaDetalleDTO, ...]


class ObtenerDetalleCita:
    def __init__(self, gateway: DetalleCitaGateway) -> None:
        self._gateway = gateway

    def execute(self, cita_id: int) -> DetalleCitaDTO:
        detalle = self._gateway.obtener_detalle_cita(cita_id)
        if detalle is None:
            raise DetalleCitaNoEncontradaError()
        return self._map_detalle(detalle)

    def _map_detalle(self, detalle: DetalleCitaRow) -> DetalleCitaDTO:
        incidencias = tuple(self._map_incidencia(item) for item in detalle.incidencias)
        return DetalleCitaDTO(
            id=detalle.id,
            fecha=detalle.fecha,
            hora_inicio=detalle.hora_inicio,
            hora_fin=detalle.hora_fin,
            estado=detalle.estado,
            sala=detalle.sala,
            medico=detalle.medico,
            paciente=detalle.paciente,
            informe=detalle.informe,
            total_incidencias=detalle.total_incidencias,
            incidencias=incidencias,
        )

    @staticmethod
    def _map_incidencia(incidencia: IncidenciaCitaRow) -> IncidenciaDetalleDTO:
        return IncidenciaDetalleDTO(
            id=incidencia.id,
            fecha_hora=incidencia.fecha_hora,
            estado=incidencia.estado,
            resumen=incidencia.resumen,
        )
