from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.citas import HitoAtencion, ModoTimestampHito


@dataclass(frozen=True, slots=True)
class EstadoBotonHitoLote:
    habilitado: bool
    tooltip_key: str | None = None


def estado_boton_hito_lote(modo: ModoTimestampHito, hito: HitoAtencion) -> EstadoBotonHitoLote:
    if modo is ModoTimestampHito.AHORA:
        return EstadoBotonHitoLote(habilitado=True)
    if hito in {HitoAtencion.CHECK_IN, HitoAtencion.INICIO_CONSULTA}:
        return EstadoBotonHitoLote(habilitado=True)
    return EstadoBotonHitoLote(
        habilitado=False,
        tooltip_key="citas.hitos.lote.programada_solo_llegada_inicio",
    )
