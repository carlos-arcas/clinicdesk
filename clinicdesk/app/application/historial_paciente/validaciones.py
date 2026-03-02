from __future__ import annotations

from datetime import timedelta

from clinicdesk.app.application.historial_paciente.dtos import ErrorValidacionDTO, ResultadoValidacionDTO
from clinicdesk.app.application.historial_paciente.filtros import FiltrosHistorialPacienteDTO

_MAX_DIAS_RANGO = 730
_MAX_TEXTO = 100
_MAX_LIMITE = 200
_MAX_LIMITE_PRESET_TODO = 50
_ESTADOS_PERMITIDOS = {
    "citas": {"PROGRAMADA", "CONFIRMADA", "REALIZADA", "NO_PRESENTADO", "CANCELADA"},
    "recetas": {"ACTIVA", "PENDIENTE", "DISPENSADA", "FINALIZADA", "ANULADA", "CANCELADA"},
}


def validar_filtros_historial_paciente(
    filtros_norm: FiltrosHistorialPacienteDTO,
    pestaña: str,
) -> ResultadoValidacionDTO:
    errores = (
        _validar_paciente(filtros_norm.paciente_id),
        _validar_rango(filtros_norm),
        _validar_texto(filtros_norm.texto),
        _validar_estados(filtros_norm.estados, pestaña),
        _validar_paginacion(filtros_norm),
    )
    errores_presentes = tuple(error for error in errores if error is not None)
    return ResultadoValidacionDTO(ok=not errores_presentes, errores=errores_presentes)


def _validar_paciente(paciente_id: int) -> ErrorValidacionDTO | None:
    if paciente_id > 0:
        return None
    return _error("historial.paciente_invalido", "historial.validacion.error.paciente_invalido", "paciente_id")


def _validar_rango(filtros: FiltrosHistorialPacienteDTO) -> ErrorValidacionDTO | None:
    if filtros.desde is None or filtros.hasta is None:
        return None
    if filtros.desde > filtros.hasta:
        return _error("historial.fechas_invertidas", "historial.validacion.error.fechas_invertidas", "rango")
    if filtros.hasta - filtros.desde <= timedelta(days=_MAX_DIAS_RANGO):
        return None
    return _error("historial.rango_demasiado_grande", "historial.validacion.error.rango_demasiado_grande", "rango")


def _validar_texto(texto: str | None) -> ErrorValidacionDTO | None:
    if texto is None or len(texto) <= _MAX_TEXTO:
        return None
    return _error("historial.texto_demasiado_largo", "historial.validacion.error.texto_demasiado_largo", "texto")


def _validar_estados(estados: tuple[str, ...] | None, pestaña: str) -> ErrorValidacionDTO | None:
    if not estados:
        return None
    permitidos = _ESTADOS_PERMITIDOS.get((pestaña or "").strip().lower(), set())
    if all(estado in permitidos for estado in estados):
        return None
    return _error("historial.estado_invalido", "historial.validacion.error.estado_invalido", "estado")


def _validar_paginacion(filtros: FiltrosHistorialPacienteDTO) -> ErrorValidacionDTO | None:
    limite = filtros.limite or 0
    offset = filtros.offset or 0
    if limite <= 0 or limite > _MAX_LIMITE or offset < 0:
        return _error("historial.paginacion_invalida", "historial.validacion.error.paginacion_invalida", "paginacion")
    if filtros.rango_preset == "TODO" and limite > _MAX_LIMITE_PRESET_TODO:
        return _error("historial.paginacion_invalida", "historial.validacion.error.paginacion_preset_todo", "paginacion")
    return None


def _error(code: str, i18n_key: str, campo: str | None) -> ErrorValidacionDTO:
    return ErrorValidacionDTO(code=code, i18n_key=i18n_key, campo=campo)
