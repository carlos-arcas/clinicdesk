from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.application.citas.atributos import sanear_columnas_citas
from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO


@dataclass(frozen=True, slots=True)
class PaginacionCitasDTO:
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class ResultadoListadoDTO:
    items: list[dict[str, object]]
    total: int


class CitasBusquedaPort(Protocol):
    def buscar_citas_listado(
        self,
        filtros_norm: FiltrosCitasDTO,
        campos_requeridos: tuple[str, ...],
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]: ...

    def buscar_citas_calendario(
        self,
        filtros_norm: FiltrosCitasDTO,
        campos_requeridos_tooltip: tuple[str, ...],
    ) -> list[dict[str, object]]: ...


@dataclass(frozen=True, slots=True)
class BuscarCitasParaLista:
    queries: CitasBusquedaPort

    def ejecutar(
        self,
        filtros_norm: FiltrosCitasDTO,
        columnas: tuple[str, ...],
        paginacion: PaginacionCitasDTO,
    ) -> ResultadoListadoDTO:
        columnas_saneadas, _ = sanear_columnas_citas(columnas)
        items, total = self.queries.buscar_citas_listado(
            filtros_norm=filtros_norm,
            campos_requeridos=columnas_saneadas,
            limit=paginacion.limit,
            offset=paginacion.offset,
        )
        return ResultadoListadoDTO(items=items, total=total)


@dataclass(frozen=True, slots=True)
class BuscarCitasParaCalendario:
    queries: CitasBusquedaPort

    def ejecutar(
        self,
        filtros_norm: FiltrosCitasDTO,
        atributos_tooltip: tuple[str, ...],
    ) -> tuple[dict[str, object], ...]:
        atributos_saneados, _ = sanear_columnas_citas(atributos_tooltip)
        items = self.queries.buscar_citas_calendario(
            filtros_norm=filtros_norm,
            campos_requeridos_tooltip=atributos_saneados,
        )
        return tuple(items)
