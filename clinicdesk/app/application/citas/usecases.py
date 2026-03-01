from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.application.citas.atributos import ATRIBUTOS_CITA
from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO


@dataclass(frozen=True, slots=True)
class PaginacionCitasDTO:
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class ResultadoBusquedaCitasDTO:
    items: list[dict[str, object]]
    total: int


class CitasBusquedaPort(Protocol):
    def buscar_para_lista(
        self,
        filtros_norm: FiltrosCitasDTO,
        paginacion: PaginacionCitasDTO,
        columnas: tuple[str, ...],
    ) -> tuple[list[dict[str, object]], int]: ...

    def buscar_para_calendario(
        self,
        filtros_norm: FiltrosCitasDTO,
        columnas: tuple[str, ...],
    ) -> list[dict[str, object]]: ...


@dataclass(frozen=True, slots=True)
class BuscarCitasParaLista:
    queries: CitasBusquedaPort

    def ejecutar(
        self,
        filtros_norm: FiltrosCitasDTO,
        paginacion: PaginacionCitasDTO,
        columnas: tuple[str, ...],
    ) -> ResultadoBusquedaCitasDTO:
        columnas_validas = _columnas_validas(columnas)
        items, total = self.queries.buscar_para_lista(filtros_norm, paginacion, columnas_validas)
        return ResultadoBusquedaCitasDTO(items=items, total=total)


@dataclass(frozen=True, slots=True)
class BuscarCitasParaCalendario:
    queries: CitasBusquedaPort

    def ejecutar(
        self,
        filtros_norm: FiltrosCitasDTO,
    ) -> list[dict[str, object]]:
        columnas = ("fecha", "hora_inicio", "hora_fin", "paciente", "medico", "sala", "estado")
        return self.queries.buscar_para_calendario(filtros_norm, _columnas_validas(columnas))


def _columnas_validas(columnas: tuple[str, ...]) -> tuple[str, ...]:
    claves = {atributo.clave for atributo in ATRIBUTOS_CITA}
    validas = tuple(col for col in columnas if col in claves)
    if validas:
        return validas
    return tuple(atributo.clave for atributo in ATRIBUTOS_CITA if atributo.visible_por_defecto)
