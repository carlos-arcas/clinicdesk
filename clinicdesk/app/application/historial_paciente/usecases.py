from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from clinicdesk.app.application.historial_paciente.atributos import (
    ATRIBUTOS_HISTORIAL_CITAS,
    ATRIBUTOS_HISTORIAL_RECETAS,
    sanear_columnas_solicitadas,
)
from clinicdesk.app.application.historial_paciente.dtos import ResumenHistorialDTO, ResultadoListadoDTO
from clinicdesk.app.application.historial_paciente.filtros import FiltrosHistorialPacienteDTO


@dataclass(frozen=True, slots=True)
class ResumenRaw:
    total_citas: int
    no_presentados: int
    total_recetas: int
    recetas_activas: int


class HistorialPacienteQueriesPort(Protocol):
    def buscar_historial_citas(
        self,
        paciente_id: int,
        desde,
        hasta,
        texto: str | None,
        estados: tuple[str, ...] | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]: ...

    def buscar_historial_recetas(
        self,
        paciente_id: int,
        desde,
        hasta,
        texto: str | None,
        estados: tuple[str, ...] | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]: ...

    def obtener_resumen_historial(self, paciente_id: int, desde, hasta) -> ResumenRaw: ...


class ObtenerResumenHistorialPaciente:
    def __init__(self, queries: HistorialPacienteQueriesPort) -> None:
        self._queries = queries

    def ejecutar(self, paciente_id: int, ventana_dias: int | None = None) -> ResumenHistorialDTO:
        desde, hasta = _resolver_ventana(ventana_dias)
        raw = self._queries.obtener_resumen_historial(paciente_id, desde, hasta)
        return ResumenHistorialDTO(
            total_citas=raw.total_citas,
            no_presentados=raw.no_presentados,
            total_recetas=raw.total_recetas,
            recetas_activas=raw.recetas_activas,
        )


class BuscarHistorialCitasPaciente:
    def __init__(self, queries: HistorialPacienteQueriesPort) -> None:
        self._queries = queries

    def ejecutar(self, filtros_norm: FiltrosHistorialPacienteDTO, columnas) -> ResultadoListadoDTO:
        columnas_saneadas, _ = sanear_columnas_solicitadas(columnas, ATRIBUTOS_HISTORIAL_CITAS)
        items, total = self._queries.buscar_historial_citas(
            paciente_id=filtros_norm.paciente_id,
            desde=filtros_norm.desde,
            hasta=filtros_norm.hasta,
            texto=filtros_norm.texto,
            estados=filtros_norm.estados,
            limit=filtros_norm.limite or 50,
            offset=filtros_norm.offset or 0,
        )
        return ResultadoListadoDTO(items=tuple(_proyectar_item(item, columnas_saneadas) for item in items), total=total)


class BuscarHistorialRecetasPaciente:
    def __init__(self, queries: HistorialPacienteQueriesPort) -> None:
        self._queries = queries

    def ejecutar(self, filtros_norm: FiltrosHistorialPacienteDTO, columnas) -> ResultadoListadoDTO:
        columnas_saneadas, _ = sanear_columnas_solicitadas(columnas, ATRIBUTOS_HISTORIAL_RECETAS)
        items, total = self._queries.buscar_historial_recetas(
            paciente_id=filtros_norm.paciente_id,
            desde=filtros_norm.desde,
            hasta=filtros_norm.hasta,
            texto=filtros_norm.texto,
            estados=filtros_norm.estados,
            limit=filtros_norm.limite or 50,
            offset=filtros_norm.offset or 0,
        )
        return ResultadoListadoDTO(items=tuple(_proyectar_item(item, columnas_saneadas) for item in items), total=total)


def _proyectar_item(item: dict[str, object], columnas: tuple[str, ...]) -> dict[str, object]:
    base = {"cita_id": item.get("cita_id"), "receta_id": item.get("receta_id")}
    base.update({columna: item.get(columna) for columna in columnas})
    return base


def _resolver_ventana(ventana_dias: int | None):
    if ventana_dias is None or ventana_dias <= 0:
        return None, None
    from datetime import datetime

    hasta = datetime.now()
    return hasta - timedelta(days=ventana_dias), hasta
