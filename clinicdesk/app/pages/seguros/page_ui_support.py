from __future__ import annotations

from clinicdesk.app.domain.seguros import EstadoOportunidadSeguro, ResultadoComercialSeguro
from clinicdesk.app.pages.seguros.cola_ui_support import popular_filtros_y_acciones


def popular_opciones_impagos(page) -> None:
    page.cmb_impagos.clear()
    page.cmb_impagos.addItem(page._i18n.t("seguros.filtros.impagos.sin_dato"), None)
    page.cmb_impagos.addItem(page._i18n.t("comun.no"), False)
    page.cmb_impagos.addItem(page._i18n.t("comun.si"), True)


def popular_seguimiento(page) -> None:
    page.cmb_estado_seguimiento.clear()
    for estado in (EstadoOportunidadSeguro.OFERTA_ENVIADA, EstadoOportunidadSeguro.EN_SEGUIMIENTO):
        page.cmb_estado_seguimiento.addItem(estado.value, estado)
    page.cmb_cierre.clear()
    for resultado in ResultadoComercialSeguro:
        page.cmb_cierre.addItem(resultado.value, resultado)


def retranslate_page(page) -> None:
    page.box_filtros.setTitle(page._i18n.t("seguros.filtros.titulo"))
    form = page.box_filtros.layout()
    form.labelForField(page.cmb_origen).setText(page._i18n.t("seguros.filtros.plan_origen"))
    form.labelForField(page.cmb_destino).setText(page._i18n.t("seguros.filtros.plan_destino"))
    form.labelForField(page.cmb_impagos).setText(page._i18n.t("seguros.filtros.impagos"))
    page.btn_analizar.setText(page._i18n.t("seguros.accion.analizar"))
    page.btn_abrir_oportunidad.setText(page._i18n.t("seguros.accion.abrir_oportunidad"))
    page.btn_preparar_oferta.setText(page._i18n.t("seguros.accion.preparar_oferta"))
    page.box_seguimiento.setTitle(page._i18n.t("seguros.seguimiento.titulo"))
    form_seg = page.box_seguimiento.layout()
    form_seg.labelForField(page.input_accion).setText(page._i18n.t("seguros.seguimiento.accion"))
    form_seg.labelForField(page.input_nota).setText(page._i18n.t("seguros.seguimiento.nota"))
    form_seg.labelForField(page.input_siguiente).setText(page._i18n.t("seguros.seguimiento.siguiente_paso"))
    form_seg.labelForField(page.cmb_estado_seguimiento).setText(page._i18n.t("seguros.seguimiento.estado"))
    form_seg.labelForField(page.cmb_cierre).setText(page._i18n.t("seguros.seguimiento.cierre"))
    page.btn_registrar_seguimiento.setText(page._i18n.t("seguros.accion.registrar_seguimiento"))
    page.btn_cerrar.setText(page._i18n.t("seguros.accion.cerrar_oportunidad"))
    page.btn_refrescar_cartera.setText(page._i18n.t("seguros.accion.refrescar_cartera"))
    page.box_cola.setTitle(page._i18n.t("seguros.cola.titulo"))
    form_cola = page.box_cola.layout()
    form_cola.labelForField(page.cmb_filtro_cola).setText(page._i18n.t("seguros.cola.filtro"))
    form_cola.labelForField(page.cmb_accion_cola).setText(page._i18n.t("seguros.cola.accion"))
    form_cola.labelForField(page.input_nota_cola).setText(page._i18n.t("seguros.cola.nota"))
    form_cola.labelForField(page.input_siguiente_cola).setText(page._i18n.t("seguros.cola.siguiente"))
    page.btn_registrar_accion_cola.setText(page._i18n.t("seguros.cola.registrar"))
    page.box_ejecutivo.setTitle(page._i18n.t("seguros.ejecutivo.titulo"))
    form_ejecutivo = page.box_ejecutivo.layout()
    form_ejecutivo.labelForField(page.lbl_resumen_ejecutivo).setText(page._i18n.t("seguros.ejecutivo.resumen_label"))
    form_ejecutivo.labelForField(page.lbl_metricas_funnel).setText(page._i18n.t("seguros.ejecutivo.metricas_label"))
    form_ejecutivo.labelForField(page.lbl_cohortes).setText(page._i18n.t("seguros.ejecutivo.cohortes_label"))
    form_ejecutivo.labelForField(page.cmb_campanias).setText(page._i18n.t("seguros.ejecutivo.campanias_label"))
    form_ejecutivo.labelForField(page.lbl_campania).setText(page._i18n.t("seguros.ejecutivo.campania_detalle_label"))
    page.btn_aplicar_campania.setText(page._i18n.t("seguros.ejecutivo.campania_aplicar"))
    popular_opciones_impagos(page)
    popular_seguimiento(page)
    popular_filtros_y_acciones(page._i18n, page.cmb_filtro_cola, page.cmb_accion_cola)
