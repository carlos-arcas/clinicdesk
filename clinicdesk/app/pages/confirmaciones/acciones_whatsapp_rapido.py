from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EstadoAccionRapidaWhatsAppDTO:
    visible: bool
    enabled: bool
    tooltip_key: str | None = None


def estado_accion_whatsapp_rapida(
    riesgo: str,
    recordatorio_estado: str,
    tiene_telefono: bool,
) -> EstadoAccionRapidaWhatsAppDTO:
    if riesgo != "ALTO":
        return EstadoAccionRapidaWhatsAppDTO(visible=False, enabled=False)
    if recordatorio_estado == "ENVIADO":
        return EstadoAccionRapidaWhatsAppDTO(
            visible=True, enabled=False, tooltip_key="confirmaciones.accion.ya_enviado"
        )
    if recordatorio_estado == "PREPARADO":
        return EstadoAccionRapidaWhatsAppDTO(
            visible=True, enabled=False, tooltip_key="confirmaciones.accion.ya_preparado"
        )
    if not tiene_telefono:
        return EstadoAccionRapidaWhatsAppDTO(
            visible=True, enabled=False, tooltip_key="confirmaciones.accion.falta_telefono"
        )
    return EstadoAccionRapidaWhatsAppDTO(visible=True, enabled=True)
