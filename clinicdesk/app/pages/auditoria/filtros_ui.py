from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from clinicdesk.app.application.auditoria_acceso import AccionAuditoriaAcceso, EntidadAuditoriaAcceso
from clinicdesk.app.application.usecases.filtros_auditoria import (
    PRESET_30_DIAS,
    PRESET_7_DIAS,
    PRESET_HOY,
    PRESET_PERSONALIZADO,
)


@dataclass(frozen=True, slots=True)
class FiltroCombo:
    texto: str
    valor: Optional[str]


def parse_fecha_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value) if value else None
    except ValueError:
        return None


def opciones_rango(traducir) -> tuple[FiltroCombo, ...]:
    return (
        FiltroCombo(traducir("auditoria.filtro.rango.hoy"), PRESET_HOY),
        FiltroCombo(traducir("auditoria.filtro.rango.7_dias"), PRESET_7_DIAS),
        FiltroCombo(traducir("auditoria.filtro.rango.30_dias"), PRESET_30_DIAS),
        FiltroCombo(traducir("auditoria.filtro.rango.personalizado"), PRESET_PERSONALIZADO),
    )


def opciones_accion(traducir) -> tuple[FiltroCombo, ...]:
    return (
        FiltroCombo(traducir("auditoria.filtro.todas"), None),
        FiltroCombo(traducir("auditoria.accion.ver_historial"), AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE.value),
        FiltroCombo(traducir("auditoria.accion.ver_detalle_cita"), AccionAuditoriaAcceso.VER_DETALLE_CITA.value),
        FiltroCombo(traducir("auditoria.accion.copiar_informe"), AccionAuditoriaAcceso.COPIAR_INFORME_CITA.value),
        FiltroCombo(traducir("auditoria.accion.ver_detalle_receta"), AccionAuditoriaAcceso.VER_DETALLE_RECETA.value),
    )


def opciones_entidad(traducir) -> tuple[FiltroCombo, ...]:
    return (
        FiltroCombo(traducir("auditoria.filtro.todas"), None),
        FiltroCombo(traducir("auditoria.entidad.paciente"), EntidadAuditoriaAcceso.PACIENTE.value),
        FiltroCombo(traducir("auditoria.entidad.cita"), EntidadAuditoriaAcceso.CITA.value),
        FiltroCombo(traducir("auditoria.entidad.receta"), EntidadAuditoriaAcceso.RECETA.value),
    )


def columnas_tabla() -> tuple[str, ...]:
    return (
        "auditoria.columna.fecha_hora",
        "auditoria.columna.usuario",
        "auditoria.columna.demo",
        "auditoria.columna.accion",
        "auditoria.columna.entidad",
        "auditoria.columna.id",
    )
