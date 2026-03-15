from __future__ import annotations

from clinicdesk.app.application.seguros.postventa import FiltroCarteraPolizaSeguro
from clinicdesk.app.application.seguros.seguridad_observabilidad import (
    snapshot_economia_poliza_segura,
    snapshot_postventa_seguro,
)
from clinicdesk.app.domain.seguros.economia_poliza import EstadoPagoPolizaSeguro, ResumenEconomicoPolizaSeguro
from clinicdesk.app.domain.seguros.postventa import EstadoPolizaSeguro, PolizaSeguro


def construir_texto_cartera_postventa(i18n, polizas: tuple[PolizaSeguro, ...]) -> str:
    if not polizas:
        return i18n.t("seguros.postventa.sin_polizas")
    lineas = [i18n.t("seguros.postventa.titulo")]
    for poliza in polizas:
        snapshot = snapshot_postventa_seguro(poliza)
        lineas.append(
            i18n.t("seguros.postventa.item").format(
                id_poliza=snapshot["id_poliza"],
                estado=snapshot["estado"],
                titular=snapshot["titular_ref"],
                beneficiarios=snapshot["beneficiarios"],
                vigencia_inicio=snapshot["vigencia_inicio"],
                vigencia_fin=snapshot["vigencia_fin"],
                renovacion=snapshot["renovacion"],
                incidencias=snapshot["incidencias"],
            )
        )
    return "\n".join(lineas)


def construir_texto_cartera_economica(i18n, resumenes: tuple[ResumenEconomicoPolizaSeguro, ...]) -> str:
    if not resumenes:
        return i18n.t("seguros.postventa.economia.sin_datos")
    lineas = [i18n.t("seguros.postventa.economia.titulo")]
    for item in resumenes:
        snapshot = snapshot_economia_poliza_segura(item)
        lineas.append(
            i18n.t("seguros.postventa.economia.item").format(
                id_poliza=snapshot["id_poliza"],
                estado=snapshot["estado"],
                riesgo=snapshot["riesgo"],
                pendiente=snapshot["pendiente_tramo"],
                emitidas=snapshot["emitidas"],
                pagadas=snapshot["pagadas"],
                vencidas=snapshot["vencidas"],
                impagadas=snapshot["impagadas"],
                motivo=snapshot["motivo"],
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
