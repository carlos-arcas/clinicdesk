from __future__ import annotations

from datetime import datetime

from clinicdesk.app.application.ports.citas_read_port import CitaReadModel, CitasReadPort
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import IncidenciasRepository


class SqliteCitasReadAdapter(CitasReadPort):
    """Adaptador de infraestructura para exponer citas al pipeline de extracción."""

    def __init__(
        self,
        citas_repo: CitasRepository,
        incidencias_repo: IncidenciasRepository,
    ) -> None:
        self._citas_repo = citas_repo
        self._incidencias_repo = incidencias_repo

    def list_in_range(self, desde: datetime, hasta: datetime) -> list[CitaReadModel]:
        citas = self._citas_repo.list_in_range(desde=desde, hasta=hasta)
        return [self._to_read_model(cita) for cita in citas]

    def _to_read_model(self, cita) -> CitaReadModel:
        return CitaReadModel(
            cita_id=str(cita.id),
            paciente_id=cita.paciente_id,
            medico_id=cita.medico_id,
            inicio=cita.inicio,
            fin=cita.fin,
            estado=cita.estado.value,
            notas=cita.notas,
            has_incidencias=self._has_incidencias(cita.id),
        )

    def _has_incidencias(self, cita_id: int | None) -> bool:
        if cita_id is None:
            return False
        return bool(self._incidencias_repo.search(cita_id=cita_id))
