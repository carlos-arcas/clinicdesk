from __future__ import annotations

from clinicdesk.app.application.seguros.postventa import FiltroCarteraPolizaSeguro
from clinicdesk.app.domain.seguros.economia_poliza import EstadoPagoPolizaSeguro, ResumenEconomicoPolizaSeguro
from clinicdesk.app.domain.seguros.postventa import EstadoPolizaSeguro, PolizaSeguro


def construir_texto_cartera_postventa(i18n, polizas: tuple[PolizaSeguro, ...]) -> str:
    if not polizas:
        return i18n.t("seguros.postventa.sin_polizas")
    lineas = [i18n.t("seguros.postventa.titulo")]
    for poliza in polizas:
        lineas.append(
            i18n.t("seguros.postventa.item").format(
                id_poliza=poliza.id_poliza,
                estado=poliza.estado.value,
                titular=poliza.titular.nombre,
                beneficiarios=len(poliza.beneficiarios),
                vigencia_inicio=poliza.vigencia.fecha_inicio.isoformat(),
                vigencia_fin=poliza.vigencia.fecha_fin.isoformat(),
                renovacion=poliza.renovacion.estado.value,
                incidencias=len(poliza.incidencias),
            )
        )
    return "\n".join(lineas)


def construir_texto_cartera_economica(i18n, resumenes: tuple[ResumenEconomicoPolizaSeguro, ...]) -> str:
    if not resumenes:
        return i18n.t("seguros.postventa.economia.sin_datos")
    lineas = [i18n.t("seguros.postventa.economia.titulo")]
    for item in resumenes:
        lineas.append(
            i18n.t("seguros.postventa.economia.item").format(
                id_poliza=item.id_poliza,
                estado=item.estado_pago.value,
                riesgo=item.nivel_riesgo.value,
                pendiente=f"{item.total_pendiente:.2f}",
                emitidas=item.cuotas_emitidas,
                pagadas=item.cuotas_pagadas,
                vencidas=item.cuotas_vencidas,
                impagadas=item.cuotas_impagadas,
                motivo=item.motivo_estado,
            )
        )
    return "\n".join(lineas)


def filtro_postventa_por_estado(valor: str | None) -> FiltroCarteraPolizaSeguro:
    if valor is None:
        return FiltroCarteraPolizaSeguro()
    return FiltroCarteraPolizaSeguro(estado=EstadoPolizaSeguro(valor))


def estado_pago_desde_selector(valor: str | None) -> EstadoPagoPolizaSeguro | None:
    if valor is None:
        return None
    return EstadoPagoPolizaSeguro(valor)
