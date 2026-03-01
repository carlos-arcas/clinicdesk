from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from clinicdesk.app.application.confirmaciones.dtos import (
    FilaConfirmacionDTO,
    FiltrosConfirmacionesDTO,
    ResultadoConfirmacionesDTO,
)
from clinicdesk.app.application.prediccion_ausencias.dtos import CitaParaPrediccionDTO
from clinicdesk.app.queries.confirmaciones_queries import (
    ConfirmacionesQueries,
    FiltrosConfirmacionesQuery,
)


@dataclass(frozen=True, slots=True)
class PaginacionConfirmacionesDTO:
    limit: int
    offset: int


@dataclass(slots=True)
class ObtenerConfirmacionesCitas:
    queries: ConfirmacionesQueries
    obtener_riesgo_uc: object
    obtener_salud_uc: object

    def ejecutar(
        self,
        filtros: FiltrosConfirmacionesDTO,
        paginacion: PaginacionConfirmacionesDTO,
    ) -> ResultadoConfirmacionesDTO:
        query_filters = FiltrosConfirmacionesQuery(
            desde=filtros.desde,
            hasta=filtros.hasta,
            texto_paciente=filtros.texto_paciente,
            recordatorio_filtro=filtros.recordatorio_filtro,
        )
        rows, total = self.queries.buscar_citas_confirmaciones(query_filters, paginacion.limit, paginacion.offset)
        riesgos = self.obtener_riesgo_uc.ejecutar([self._to_cita_prediccion(row) for row in rows])
        items = [
            FilaConfirmacionDTO(
                cita_id=row.cita_id,
                inicio=row.inicio,
                paciente=row.paciente_nombre,
                medico=row.medico_nombre,
                estado_cita=row.estado_cita,
                riesgo=riesgos.get(row.cita_id, "NO_DISPONIBLE"),
                recordatorio_estado=row.recordatorio_estado_global,
            )
            for row in rows
        ]
        items_filtrados = self._filtrar_por_riesgo(items, filtros.riesgo_filtro)
        salud = self.obtener_salud_uc.ejecutar()
        return ResultadoConfirmacionesDTO(
            total=total,
            mostrados=len(items_filtrados),
            items=items_filtrados,
            salud_prediccion=salud,
        )

    @staticmethod
    def _to_cita_prediccion(row) -> CitaParaPrediccionDTO:
        inicio_dt = datetime.fromisoformat(row.inicio)
        antelacion = max((inicio_dt.date() - date.today()).days, 0)
        return CitaParaPrediccionDTO(
            id=row.cita_id,
            fecha=inicio_dt.date().isoformat(),
            hora=inicio_dt.time().strftime("%H:%M"),
            paciente_id=row.paciente_id,
            medico_id=row.medico_id,
            antelacion_dias=antelacion,
        )

    @staticmethod
    def _filtrar_por_riesgo(items: list[FilaConfirmacionDTO], riesgo_filtro: str) -> list[FilaConfirmacionDTO]:
        riesgo = riesgo_filtro.upper().strip()
        if riesgo == "SOLO_ALTO":
            return [item for item in items if item.riesgo == "ALTO"]
        if riesgo == "ALTO_MEDIO":
            return [item for item in items if item.riesgo in {"ALTO", "MEDIO"}]
        return items
