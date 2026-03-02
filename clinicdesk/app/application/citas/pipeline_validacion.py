from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO, normalizar_filtros_citas
from clinicdesk.app.application.citas.validaciones import (
    ContextoValidacionCitas,
    ResultadoValidacionDTO,
    validar_filtros_citas,
)


@dataclass(frozen=True, slots=True)
class ResultadoPipelineFiltrosCitasDTO:
    filtros_normalizados: FiltrosCitasDTO
    validacion: ResultadoValidacionDTO


def normalizar_y_validar_filtros_citas(
    filtros: FiltrosCitasDTO,
    ahora: datetime,
    contexto: ContextoValidacionCitas,
) -> ResultadoPipelineFiltrosCitasDTO:
    filtros_norm = normalizar_filtros_citas(filtros, ahora)
    validacion = validar_filtros_citas(filtros_norm, contexto)
    return ResultadoPipelineFiltrosCitasDTO(filtros_normalizados=filtros_norm, validacion=validacion)
