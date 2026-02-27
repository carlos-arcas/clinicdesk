from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.application.ports.citas_read_port import CitaReadModel, CitasReadPort


@dataclass(slots=True)
class CitasDatasetRow:
    cita_id: str
    paciente_id: int
    medico_id: int
    inicio: datetime
    fin: datetime
    duracion_min: int
    estado: str
    has_incidencias: bool
    notas_len: int


class CitasDatasetBuildError(ValueError):
    """Error base del pipeline de extracción de citas."""


class InvalidCitaTimeRangeError(CitasDatasetBuildError):
    """Se dispara cuando una cita trae un rango temporal inválido."""


Dataset = list[CitasDatasetRow]


class BuildCitasDataset:
    """Caso de uso de application para construir el dataset tabular de citas."""

    def __init__(self, citas_read_port: CitasReadPort) -> None:
        self._citas_read_port = citas_read_port

    def execute(self, desde: datetime, hasta: datetime) -> Dataset:
        self._validate_requested_range(desde, hasta)
        citas = self._citas_read_port.list_in_range(desde, hasta)
        filtered = self._filter_by_requested_range(citas, desde, hasta)
        return [self._to_dataset_row(cita) for cita in filtered]

    def _validate_requested_range(self, desde: datetime, hasta: datetime) -> None:
        if hasta < desde:
            raise CitasDatasetBuildError("Rango inválido: 'hasta' no puede ser menor que 'desde'.")

    def _filter_by_requested_range(
        self,
        citas: list[CitaReadModel],
        desde: datetime,
        hasta: datetime,
    ) -> list[CitaReadModel]:
        return [cita for cita in citas if desde <= cita.inicio <= hasta]

    def _to_dataset_row(self, cita: CitaReadModel) -> CitasDatasetRow:
        duration = self._duration_minutes(cita)
        return CitasDatasetRow(
            cita_id=cita.cita_id,
            paciente_id=cita.paciente_id,
            medico_id=cita.medico_id,
            inicio=cita.inicio,
            fin=cita.fin,
            duracion_min=duration,
            estado=cita.estado,
            has_incidencias=bool(cita.has_incidencias),
            notas_len=len((cita.notas or "").strip()),
        )

    def _duration_minutes(self, cita: CitaReadModel) -> int:
        delta_minutes = int((cita.fin - cita.inicio).total_seconds() // 60)
        if delta_minutes < 0:
            raise InvalidCitaTimeRangeError(
                f"Cita '{cita.cita_id}' inválida: fin ({cita.fin}) anterior a inicio ({cita.inicio})."
            )
        return delta_minutes
