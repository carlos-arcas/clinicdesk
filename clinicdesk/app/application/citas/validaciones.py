from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO


ContextoValidacionCitas = Literal["LISTA", "CALENDARIO"]
_ESTADOS_VALIDOS = {"PROGRAMADA", "CONFIRMADA", "CANCELADA", "REALIZADA", "NO_PRESENTADO"}
_FILTROS_CALIDAD_VALIDOS = {"SIN_CHECKIN", "SIN_INICIO_FIN", "SIN_SALIDA"}
_MAX_RANGO_DIAS = {"LISTA": 365, "CALENDARIO": 90}


@dataclass(frozen=True, slots=True)
class ErrorValidacionDTO:
    code: str
    i18n_key: str
    campo: str | None = None


@dataclass(frozen=True, slots=True)
class ResultadoValidacionDTO:
    ok: bool
    errores: tuple[ErrorValidacionDTO, ...]


def validar_filtros_citas(
    filtros_norm: FiltrosCitasDTO,
    contexto: ContextoValidacionCitas,
) -> ResultadoValidacionDTO:
    errores = [
        *list(_validar_fechas(filtros_norm, contexto)),
        *_validar_texto_busqueda(filtros_norm.texto_busqueda),
        *_validar_estado(filtros_norm.estado_cita),
        *_validar_ids(filtros_norm),
        *_validar_filtro_calidad(filtros_norm.filtro_calidad),
        *_validar_paginacion(filtros_norm.limit, filtros_norm.offset),
    ]
    return ResultadoValidacionDTO(ok=not errores, errores=tuple(errores))


def _validar_fechas(
    filtros_norm: FiltrosCitasDTO,
    contexto: ContextoValidacionCitas,
) -> tuple[ErrorValidacionDTO, ...]:
    desde = filtros_norm.desde
    hasta = filtros_norm.hasta
    if desde is None or hasta is None:
        return ()
    if desde > hasta:
        return (
            ErrorValidacionDTO("citas.fechas_invertidas", "citas.validacion.fechas_invertidas", "desde"),
        )
    return _validar_rango_maximo(desde, hasta, contexto)


def _validar_rango_maximo(desde: datetime, hasta: datetime, contexto: ContextoValidacionCitas) -> tuple[ErrorValidacionDTO, ...]:
    maximo = _MAX_RANGO_DIAS[contexto]
    rango_dias = (hasta - desde).days
    if rango_dias <= maximo:
        return ()
    return (
        ErrorValidacionDTO("citas.rango_demasiado_grande", "citas.validacion.rango_demasiado_grande", "hasta"),
    )


def _validar_texto_busqueda(texto: str | None) -> tuple[ErrorValidacionDTO, ...]:
    if texto is None or len(texto) <= 100:
        return ()
    return (
        ErrorValidacionDTO("citas.texto_demasiado_largo", "citas.validacion.texto_demasiado_largo", "texto_busqueda"),
    )


def _validar_estado(estado_cita: str | None) -> tuple[ErrorValidacionDTO, ...]:
    if estado_cita is None or estado_cita in _ESTADOS_VALIDOS:
        return ()
    return (ErrorValidacionDTO("citas.estado_invalido", "citas.validacion.estado_invalido", "estado_cita"),)


def _validar_ids(filtros_norm: FiltrosCitasDTO) -> tuple[ErrorValidacionDTO, ...]:
    campos = {
        "medico_id": filtros_norm.medico_id,
        "sala_id": filtros_norm.sala_id,
        "paciente_id": filtros_norm.paciente_id,
    }
    for campo, valor in campos.items():
        if valor is not None and valor <= 0:
            return (ErrorValidacionDTO("citas.id_invalido", "citas.validacion.id_invalido", campo),)
    return ()



def _validar_filtro_calidad(filtro_calidad: str | None) -> tuple[ErrorValidacionDTO, ...]:
    if filtro_calidad is None or filtro_calidad in _FILTROS_CALIDAD_VALIDOS:
        return ()
    return (
        ErrorValidacionDTO("citas.filtro_calidad_invalido", "citas.validacion.filtro_calidad_invalido", "filtro_calidad"),
    )

def _validar_paginacion(limit: int, offset: int) -> tuple[ErrorValidacionDTO, ...]:
    if limit <= 200 and offset >= 0:
        return ()
    return (
        ErrorValidacionDTO("citas.paginacion_invalida", "citas.validacion.paginacion_invalida", None),
    )
