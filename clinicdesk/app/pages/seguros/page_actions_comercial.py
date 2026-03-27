from __future__ import annotations

from clinicdesk.app.application.seguros import (
    SolicitudCrearCampaniaDesdeSugerencia,
    SolicitudGestionItemCampaniaSeguro,
    SolicitudGestionItemColaSeguro,
)
from clinicdesk.app.domain.seguros import EstadoItemCampaniaSeguro, ResultadoItemCampaniaSeguro
from clinicdesk.app.pages.seguros.agenda_ui_support import (
    construir_texto_acciones_rapidas,
    construir_texto_alertas_activas,
    construir_texto_bloqueos,
    construir_texto_cierre_semanal,
    construir_texto_plan_semanal,
    construir_texto_recomendacion_cierre,
    construir_texto_tareas_vencidas,
)
from clinicdesk.app.pages.seguros.analitica_ui_support import (
    construir_texto_aprendizaje,
    construir_texto_campania_activa,
    construir_texto_cohortes,
    construir_texto_forecast,
    construir_texto_metricas_funnel,
    construir_texto_resumen_ejecutivo,
    construir_texto_valor_economico,
    poblar_selector_campanias,
)
from clinicdesk.app.pages.seguros.campanias_ui_support import (
    construir_texto_resultado_campania,
    poblar_selector_campanias_ejecutables,
    poblar_selector_items_campania,
)
from clinicdesk.app.pages.seguros.cola_operaciones import construir_panel_operativo, construir_resumen_cartera
from clinicdesk.app.pages.seguros.page_actions_postventa import refrescar_postventa


def registrar_seguimiento(page) -> None:
    if not page._id_oportunidad_activa:
        return
    oportunidad = page._gestion.registrar_seguimiento(
        page._id_oportunidad_activa,
        page.cmb_estado_seguimiento.currentData(),
        page.input_accion.text().strip() or "seguimiento",
        page.input_nota.text().strip() or "-",
        page.input_siguiente.text().strip() or "-",
    )
    page.lbl_estado_comercial.setText(
        page._i18n.t("seguros.comercial.estado").format(
            estado=oportunidad.estado_actual.value,
            motor=oportunidad.clasificacion_motor,
            fit=oportunidad.evaluacion_fit.encaje_plan.value if oportunidad.evaluacion_fit else "-",
        )
    )


def cerrar_oportunidad(page) -> None:
    if not page._id_oportunidad_activa:
        return
    oportunidad = page._gestion.cerrar_oportunidad(page._id_oportunidad_activa, page.cmb_cierre.currentData())
    renovaciones = page._gestion.listar_renovaciones_pendientes()
    page.lbl_estado_comercial.setText(
        page._i18n.t("seguros.comercial.cierre").format(
            estado=oportunidad.estado_actual.value,
            resultado=oportunidad.resultado_comercial.value if oportunidad.resultado_comercial else "-",
        )
    )
    page.lbl_renovaciones.setText(
        page._i18n.t("seguros.comercial.renovaciones_pendientes").format(cantidad=len(renovaciones))
    )
    refrescar_cartera(page)


def refrescar_cartera(page) -> None:
    resumen, caliente, abiertas = construir_resumen_cartera(page._i18n, page._gestion, page._scoring)
    renovaciones = page._gestion.listar_renovaciones_pendientes()
    page.lbl_cartera.setText(resumen)
    page.lbl_renovaciones.setText(
        page._i18n.t("seguros.comercial.renovaciones_pendientes").format(cantidad=len(renovaciones))
    )
    _actualizar_recomendacion(page, abiertas, caliente)
    _actualizar_panel_operativo(page)
    _actualizar_estado_comercial(page, abiertas)
    _actualizar_agenda(page)
    _actualizar_panel_analitico(page)
    refrescar_campanias_ejecutables(page)
    refrescar_postventa(page)


def _actualizar_recomendacion(page, abiertas, caliente: str | None) -> None:
    oportunidad = next((item for item in abiertas if item.id_oportunidad == caliente), None)
    if not oportunidad:
        page.lbl_recomendacion.setText(page._i18n.t("seguros.recomendacion.sin_dato"))
        return
    diagnostico = page._recomendador.evaluar_oportunidad(oportunidad)
    page.lbl_recomendacion.setText(
        page._i18n.t("seguros.recomendacion.resumen").format(
            plan=diagnostico.recomendacion_plan.plan_recomendado_id or "-",
            riesgo=diagnostico.riesgo_renovacion.semaforo.value,
            argumento=diagnostico.argumento_comercial.angulo_principal,
            accion=diagnostico.accion_retencion.accion_sugerida,
            cautela=diagnostico.recomendacion_plan.cautela,
        )
    )


def _actualizar_panel_operativo(page) -> None:
    cola_txt, historial_txt, activa = construir_panel_operativo(
        page._i18n,
        page._repositorio,
        page._cola,
        page._id_oportunidad_activa,
        page.cmb_filtro_cola.currentData(),
    )
    page.lbl_cola_operativa.setText(cola_txt)
    page.lbl_historial_operativo.setText(historial_txt)
    page._id_oportunidad_activa = activa


def _actualizar_estado_comercial(page, abiertas) -> None:
    oportunidad = next((item for item in abiertas if item.id_oportunidad == page._id_oportunidad_activa), None)
    if oportunidad is None:
        page.lbl_estado_comercial.setText(page._i18n.t("seguros.comercial.sin_oportunidad"))
        return
    page.lbl_estado_comercial.setText(
        page._i18n.t("seguros.comercial.estado").format(
            estado=oportunidad.estado_actual.value,
            motor=oportunidad.clasificacion_motor,
            fit=oportunidad.evaluacion_fit.encaje_plan.value if oportunidad.evaluacion_fit else "-",
        )
    )


def _actualizar_agenda(page) -> None:
    plan = page._agenda.construir_plan_semanal()
    page.lbl_alertas_activas.setText(construir_texto_alertas_activas(page._i18n, plan))
    page.lbl_plan_semanal.setText(construir_texto_plan_semanal(page._i18n, plan))
    page.lbl_tareas_vencidas.setText(construir_texto_tareas_vencidas(page._i18n, plan))
    page.lbl_acciones_rapidas.setText(construir_texto_acciones_rapidas(page._i18n, plan))
    resumen_semana = page._cierre_semanal.construir_resumen_semana()
    page.lbl_cierre_semanal.setText(construir_texto_cierre_semanal(page._i18n, resumen_semana))
    page.lbl_bloqueos_recurrentes.setText(construir_texto_bloqueos(page._i18n, resumen_semana))
    page.lbl_recomendacion_cierre.setText(construir_texto_recomendacion_cierre(page._i18n, resumen_semana))


def _actualizar_panel_analitico(page) -> None:
    resumen = page._analitica.construir_resumen()
    page.lbl_resumen_ejecutivo.setText(construir_texto_resumen_ejecutivo(page._i18n, resumen))
    page.lbl_metricas_funnel.setText(construir_texto_metricas_funnel(page._i18n, resumen))
    page.lbl_cohortes.setText(construir_texto_cohortes(page._i18n, resumen))
    page.lbl_aprendizaje.setText(construir_texto_aprendizaje(page._i18n, page._aprendizaje.construir_panel()))
    page.lbl_valor_economico.setText(construir_texto_valor_economico(page._i18n, resumen))
    page.lbl_forecast.setText(construir_texto_forecast(page._i18n, resumen))
    poblar_selector_campanias(page._i18n, page.cmb_campanias, resumen)
    actualizar_detalle_campania(page, resumen)


def actualizar_detalle_campania(page, resumen_ejecutivo) -> None:
    id_campania = page.cmb_campanias.currentData()
    if not id_campania and resumen_ejecutivo.campanias:
        id_campania = resumen_ejecutivo.campanias[0].id_campania
    page.lbl_campania.setText(construir_texto_campania_activa(page._i18n, resumen_ejecutivo, str(id_campania or "")))


def aplicar_campania(page) -> None:
    id_campania = page.cmb_campanias.currentData()
    if not id_campania:
        return
    ids = page._analitica.ids_oportunidad_por_campania(str(id_campania))
    if ids:
        page._id_oportunidad_activa = ids[0]
    refrescar_cartera(page)


def registrar_accion_cola(page) -> None:
    if not page._id_oportunidad_activa:
        return
    page._cola.registrar_gestion(
        SolicitudGestionItemColaSeguro(
            id_oportunidad=page._id_oportunidad_activa,
            accion=page.cmb_accion_cola.currentData(),
            nota_corta=page.input_nota_cola.text().strip(),
            siguiente_paso=page.input_siguiente_cola.text().strip(),
        )
    )
    refrescar_cartera(page)


def crear_campania_desde_sugerencia(page) -> None:
    id_campania = page.cmb_campanias.currentData()
    if not id_campania:
        return
    resumen = page._analitica.construir_resumen()
    sugerencia = next((c for c in resumen.campanias if c.id_campania == id_campania), None)
    if sugerencia is None:
        return
    nueva = f"exec-{id_campania}-{len(page._campanias.listar_campanias()) + 1}"
    page._campanias.crear_desde_sugerencia(
        SolicitudCrearCampaniaDesdeSugerencia(
            id_campania_nueva=nueva,
            objetivo_comercial=page._i18n.t("seguros.campania.objetivo_default"),
            sugerencia=sugerencia,
        )
    )
    refrescar_campanias_ejecutables(page)


def refrescar_campanias_ejecutables(page) -> None:
    campanias = page._campanias.listar_campanias()
    poblar_selector_campanias_ejecutables(page._i18n, page.cmb_campanias_ejecutables, campanias)
    poblar_estados_items_campania(page)
    id_campania = page.cmb_campanias_ejecutables.currentData() or (campanias[0].id_campania if campanias else None)
    if not id_campania:
        page.lbl_resultado_campania.setText(page._i18n.t("seguros.campania.sin_dato"))
        return
    campania, items = page._campanias.obtener_detalle(str(id_campania))
    poblar_selector_items_campania(page._i18n, page.cmb_items_campania, items)
    page.lbl_resultado_campania.setText(construir_texto_resultado_campania(page._i18n, campania))


def registrar_item_campania(page) -> None:
    id_campania = page.cmb_campanias_ejecutables.currentData()
    id_item = page.cmb_items_campania.currentData()
    if not id_campania or not id_item:
        return
    page._campanias.registrar_resultado_item(
        SolicitudGestionItemCampaniaSeguro(
            id_campania=str(id_campania),
            id_item=str(id_item),
            estado_trabajo=page.cmb_estado_item_campania.currentData(),
            accion_tomada=page.input_accion_item_campania.text().strip(),
            resultado=page.cmb_resultado_item_campania.currentData(),
            nota_corta=page.input_nota_item_campania.text().strip(),
        )
    )
    refrescar_campanias_ejecutables(page)


def poblar_estados_items_campania(page) -> None:
    page.cmb_estado_item_campania.clear()
    for estado in EstadoItemCampaniaSeguro:
        page.cmb_estado_item_campania.addItem(estado.value, estado)
    page.cmb_resultado_item_campania.clear()
    for resultado in ResultadoItemCampaniaSeguro:
        page.cmb_resultado_item_campania.addItem(resultado.value, resultado)
