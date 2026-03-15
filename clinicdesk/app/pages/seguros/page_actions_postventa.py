from __future__ import annotations

from datetime import date

from clinicdesk.app.application.seguros import (
    FiltroCarteraEconomicaPolizaSeguro,
    FiltroCarteraPolizaSeguro,
    SolicitudAltaPolizaDesdeConversion,
    SolicitudEmitirCuotaPolizaSeguro,
    SolicitudRegistrarImpagoSeguro,
    SolicitudRegistrarIncidenciaPoliza,
    SolicitudRegistrarPagoCuotaSeguro,
    SolicitudRegistrarReactivacionPolizaSeguro,
    SolicitudRegistrarSuspensionPolizaSeguro,
)
from clinicdesk.app.domain.seguros.postventa import (
    BeneficiarioSeguro,
    EstadoAseguradoSeguro,
    TipoIncidenciaPolizaSeguro,
)
from clinicdesk.app.pages.seguros.postventa_ui_support import (
    construir_texto_cartera_economica,
    construir_texto_cartera_postventa,
    estado_pago_desde_selector,
)


def materializar_poliza(page) -> None:
    if not page._id_oportunidad_activa:
        return
    nombre_titular = page.input_nombre_titular.text().strip() or page._i18n.t("seguros.postventa.titular_default")
    documento = page.input_doc_titular.text().strip() or page._i18n.t("seguros.postventa.documento_default")
    nombre_beneficiario = page.input_nombre_beneficiario.text().strip()
    beneficiarios = ()
    if nombre_beneficiario:
        beneficiarios = (
            BeneficiarioSeguro(
                id_beneficiario=f"ben-{page._id_oportunidad_activa}",
                nombre=nombre_beneficiario,
                parentesco="familiar",
                estado=EstadoAseguradoSeguro.ACTIVO,
            ),
        )
    page._postventa.materializar_poliza_desde_conversion(
        SolicitudAltaPolizaDesdeConversion(
            id_oportunidad=page._id_oportunidad_activa,
            id_poliza=f"pol-{page._id_oportunidad_activa}",
            nombre_titular=nombre_titular,
            documento_titular=documento,
            fecha_inicio=date.today(),
            beneficiarios=beneficiarios,
        )
    )
    refrescar_postventa(page)


def registrar_incidencia_poliza(page) -> None:
    if not page._id_oportunidad_activa:
        return
    id_poliza = f"pol-{page._id_oportunidad_activa}"
    page._postventa.registrar_incidencia(
        SolicitudRegistrarIncidenciaPoliza(
            id_poliza=id_poliza,
            id_incidencia=f"inc-{id_poliza}",
            tipo=page.cmb_tipo_incidencia.currentData(),
            descripcion=page._i18n.t("seguros.postventa.incidencia_default"),
            fecha_apertura=date.today(),
        )
    )
    refrescar_postventa(page)


def emitir_cuota_postventa(page) -> None:
    if not page._id_oportunidad_activa:
        return
    id_poliza = f"pol-{page._id_oportunidad_activa}"
    periodo = page.input_periodo_cuota.text().strip() or date.today().strftime("%Y-%m")
    importe_txt = page.input_importe_cuota.text().strip()
    importe = float(importe_txt) if importe_txt else 120.0
    page._economia_poliza.emitir_cuota(
        SolicitudEmitirCuotaPolizaSeguro(
            id_cuota=f"cuota-{id_poliza}-{periodo}",
            id_poliza=id_poliza,
            periodo=periodo,
            fecha_emision=date.today(),
            fecha_vencimiento=date.today(),
            importe=importe,
        )
    )
    refrescar_postventa(page)


def registrar_pago_cuota_postventa(page) -> None:
    if not page._id_oportunidad_activa:
        return
    cuotas = page._repo_economia_poliza.listar_cuotas_poliza(f"pol-{page._id_oportunidad_activa}")
    if cuotas:
        page._economia_poliza.registrar_pago_cuota(
            SolicitudRegistrarPagoCuotaSeguro(id_cuota=cuotas[-1].id_cuota, fecha_pago=date.today())
        )
        refrescar_postventa(page)


def registrar_impago_postventa(page) -> None:
    if not page._id_oportunidad_activa:
        return
    id_poliza = f"pol-{page._id_oportunidad_activa}"
    cuotas = page._repo_economia_poliza.listar_cuotas_poliza(id_poliza)
    if not cuotas:
        return
    cuota = cuotas[-1]
    page._economia_poliza.registrar_impago(
        SolicitudRegistrarImpagoSeguro(
            id_evento=f"imp-{cuota.id_cuota}",
            id_poliza=id_poliza,
            id_cuota=cuota.id_cuota,
            fecha_evento=date.today(),
            motivo="Impago operativo registrado por backoffice",
        )
    )
    refrescar_postventa(page)


def suspender_poliza_postventa(page) -> None:
    if not page._id_oportunidad_activa:
        return
    id_poliza = f"pol-{page._id_oportunidad_activa}"
    page._economia_poliza.registrar_suspension(
        SolicitudRegistrarSuspensionPolizaSeguro(
            id_evento=f"sus-{id_poliza}",
            id_poliza=id_poliza,
            fecha_evento=date.today(),
            motivo="Suspension operativa por riesgo economico alto",
        )
    )
    refrescar_postventa(page)


def reactivar_poliza_postventa(page) -> None:
    if not page._id_oportunidad_activa:
        return
    id_poliza = f"pol-{page._id_oportunidad_activa}"
    page._economia_poliza.registrar_reactivacion(
        SolicitudRegistrarReactivacionPolizaSeguro(
            id_evento=f"rea-{id_poliza}",
            id_poliza=id_poliza,
            fecha_evento=date.today(),
            motivo="Reactivacion por regularizacion economica",
        )
    )
    refrescar_postventa(page)


def refrescar_postventa(page) -> None:
    polizas = page._postventa.listar_cartera(FiltroCarteraPolizaSeguro())
    page.lbl_postventa.setText(construir_texto_cartera_postventa(page._i18n, polizas))
    estado_pago = estado_pago_desde_selector(page.cmb_estado_pago_filtro.currentData())
    filtro = FiltroCarteraEconomicaPolizaSeguro(estado_pago=estado_pago) if estado_pago else None
    cartera = page._economia_poliza.listar_cartera_economica(filtro)
    page.lbl_postventa_economia.setText(construir_texto_cartera_economica(page._i18n, cartera))


def poblar_tipos_incidencia(page) -> None:
    page.cmb_tipo_incidencia.clear()
    for tipo in TipoIncidenciaPolizaSeguro:
        page.cmb_tipo_incidencia.addItem(tipo.value, tipo)
