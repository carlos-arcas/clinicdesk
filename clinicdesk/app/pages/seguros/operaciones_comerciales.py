from __future__ import annotations

from clinicdesk.app.application.seguros import SolicitudAnalisisMigracionSeguro, SolicitudNuevaOportunidadSeguro
from clinicdesk.app.domain.seguros import (
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    OrigenClienteSeguro,
    SegmentoClienteSeguro,
    SensibilidadPrecioSeguro,
)


def analizar_actual(page) -> None:
    solicitud = SolicitudAnalisisMigracionSeguro(
        plan_origen_id=str(page.cmb_origen.currentData()),
        plan_destino_id=str(page.cmb_destino.currentData()),
        edad=34,
        residencia_pais="ES",
        historial_impagos=page.cmb_impagos.currentData(),
        preexistencias_graves=False,
    )
    respuesta = page._use_case.execute(solicitud)
    simulacion = respuesta.simulacion
    page.lbl_resumen.setText(
        page._i18n.t("seguros.resultado.resumen").format(
            clasificacion=simulacion.clasificacion,
            texto=simulacion.resumen_ejecutivo,
        )
    )
    page.lbl_detalle.setText(
        page._i18n.t("seguros.resultado.detalle").format(
            mejoras=", ".join(simulacion.impactos_positivos) or "-",
            perdidas=", ".join(simulacion.impactos_negativos) or "-",
            advertencias=", ".join(simulacion.advertencias) or "-",
        )
    )


def abrir_oportunidad_actual(page) -> None:
    id_oportunidad = f"opp-{page.cmb_origen.currentIndex()}-{page.cmb_destino.currentIndex()}"
    oportunidad = page._gestion.abrir_oportunidad(
        SolicitudNuevaOportunidadSeguro(
            id_oportunidad=id_oportunidad,
            id_candidato=f"cand-{id_oportunidad}",
            id_paciente="paciente-demo",
            segmento_cliente=SegmentoClienteSeguro.ASEGURADO_EXTERNO_MIGRAR,
            origen_cliente=OrigenClienteSeguro.MOSTRADOR_CLINICA,
            necesidad_principal=NecesidadPrincipalSeguro.AHORRO_COSTE,
            motivaciones=(MotivacionCompraSeguro.MEJOR_RELACION_CALIDAD_PRECIO,),
            objecion_principal=ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO,
            sensibilidad_precio=SensibilidadPrecioSeguro.MEDIA,
            friccion_migracion=FriccionMigracionSeguro.MEDIA,
            plan_origen_id=str(page.cmb_origen.currentData()),
            plan_destino_id=str(page.cmb_destino.currentData()),
        )
    )
    page._id_oportunidad_activa = oportunidad.id_oportunidad
    page.lbl_estado_comercial.setText(
        page._i18n.t("seguros.comercial.estado").format(
            estado=oportunidad.estado_actual.value,
            motor=oportunidad.clasificacion_motor,
            fit=oportunidad.evaluacion_fit.encaje_plan.value if oportunidad.evaluacion_fit else "-",
        )
    )


def preparar_oferta_actual(page) -> None:
    if not page._id_oportunidad_activa:
        return
    oferta = page._gestion.preparar_oferta(page._id_oportunidad_activa, ("nota_operativa",))
    page.lbl_detalle.setText(
        page._i18n.t("seguros.comercial.oferta").format(
            plan=oferta.plan_propuesto_id,
            clasificacion=oferta.clasificacion_migracion,
            valor=oferta.resumen_valor,
        )
    )
