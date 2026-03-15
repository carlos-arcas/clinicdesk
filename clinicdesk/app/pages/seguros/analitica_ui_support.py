from __future__ import annotations

from clinicdesk.app.application.seguros import PanelAprendizajeComercialSeguro, ResumenEjecutivoSeguros
from clinicdesk.app.i18n import I18nManager


def construir_texto_resumen_ejecutivo(i18n: I18nManager, resumen: ResumenEjecutivoSeguros) -> str:
    ratio = _render_ratio(i18n, resumen.ratio_conversion_global)
    return i18n.t("seguros.ejecutivo.resumen").format(
        total=resumen.total_oportunidades,
        abiertas=resumen.oportunidades_abiertas,
        convertidas=resumen.convertidas,
        rechazadas=resumen.rechazadas,
        pospuestas=resumen.pospuestas,
        ratio=ratio,
        renovaciones=resumen.renovaciones_pendientes,
        renovaciones_riesgo=resumen.renovaciones_en_riesgo,
    )


def construir_texto_metricas_funnel(i18n: I18nManager, resumen: ResumenEjecutivoSeguros) -> str:
    lineas = [i18n.t("seguros.ejecutivo.metricas_titulo")]
    for metrica in resumen.metrica_funnel:
        lineas.append(
            i18n.t("seguros.ejecutivo.metrica_item").format(
                clave=metrica.clave,
                valor=metrica.valor,
                ratio=_render_ratio(i18n, metrica.ratio),
                riesgo=metrica.riesgo_u_oportunidad,
                accion=metrica.accion_sugerida,
            )
        )
    return "\n".join(lineas)


def construir_texto_cohortes(i18n: I18nManager, resumen: ResumenEjecutivoSeguros) -> str:
    lineas = [i18n.t("seguros.ejecutivo.cohortes_titulo")]
    for cohorte in resumen.cohortes:
        lineas.append(
            i18n.t("seguros.ejecutivo.cohorte_item").format(
                dimension=cohorte.dimension,
                nombre=cohorte.nombre,
                tamano=cohorte.tamano,
                tasa=_render_ratio(i18n, cohorte.tasa_conversion),
                friccion=cohorte.friccion_principal,
                oportunidad=cohorte.oportunidad_principal,
                accion=cohorte.accion_sugerida,
            )
        )
    return "\n".join(lineas)


def construir_texto_campania_activa(i18n: I18nManager, resumen: ResumenEjecutivoSeguros, id_campania: str) -> str:
    campania = next((item for item in resumen.campanias if item.id_campania == id_campania), None)
    if campania is None:
        return i18n.t("seguros.ejecutivo.campania_sin_dato")
    return i18n.t("seguros.ejecutivo.campania_detalle").format(
        titulo=campania.titulo,
        criterio=campania.criterio,
        tamano=campania.tamano_estimado,
        motivo=campania.motivo,
        accion=campania.accion_recomendada,
        cautela=campania.cautela,
        ids=", ".join(campania.ids_oportunidad) or "-",
    )


def poblar_selector_campanias(i18n: I18nManager, combo, resumen: ResumenEjecutivoSeguros) -> None:
    combo.clear()
    for campania in resumen.campanias:
        texto = i18n.t("seguros.ejecutivo.campania_selector").format(
            titulo=campania.titulo,
            tamano=campania.tamano_estimado,
        )
        combo.addItem(texto, campania.id_campania)


def construir_texto_aprendizaje(i18n: I18nManager, panel: PanelAprendizajeComercialSeguro) -> str:
    lineas = [i18n.t("seguros.aprendizaje.titulo")]
    lineas.extend(_lineas_campanias(i18n, panel))
    lineas.extend(_lineas_segmentos(i18n, panel))
    lineas.extend(_lineas_argumentos(i18n, panel))
    lineas.extend(_lineas_planes(i18n, panel))
    lineas.extend(_lineas_playbooks(i18n, panel))
    return "\n".join(lineas)


def _lineas_campanias(i18n: I18nManager, panel: PanelAprendizajeComercialSeguro) -> list[str]:
    lineas = [i18n.t("seguros.aprendizaje.campanias")]
    for item in panel.efectividad_campanias[:3]:
        lineas.append(
            i18n.t("seguros.aprendizaje.campania_item").format(
                nombre=item.nombre_campania,
                senal=item.senal_efectividad,
                metrica=_render_ratio(i18n, item.metrica_principal),
                muestra=item.tamano_muestra,
                cautela=item.cautela_muestral,
            )
        )
    return lineas


def _lineas_segmentos(i18n: I18nManager, panel: PanelAprendizajeComercialSeguro) -> list[str]:
    lineas = [i18n.t("seguros.aprendizaje.segmentos")]
    for item in panel.insights_segmentos[:3]:
        lineas.append(
            i18n.t("seguros.aprendizaje.segmento_item").format(
                eje=item.eje,
                valor=item.valor,
                metrica=_render_ratio(i18n, item.metrica_principal),
                muestra=item.tamano_muestra,
                cautela=item.cautela_muestral,
            )
        )
    return lineas


def _lineas_argumentos(i18n: I18nManager, panel: PanelAprendizajeComercialSeguro) -> list[str]:
    lineas = [i18n.t("seguros.aprendizaje.argumentos")]
    for item in panel.insights_argumentos[:3]:
        lineas.append(
            i18n.t("seguros.aprendizaje.argumento_item").format(
                segmento=item.segmento,
                argumento=item.argumento,
                metrica=_render_ratio(i18n, item.metrica_principal),
                muestra=item.tamano_muestra,
            )
        )
    return lineas


def _lineas_planes(i18n: I18nManager, panel: PanelAprendizajeComercialSeguro) -> list[str]:
    lineas = [i18n.t("seguros.aprendizaje.planes")]
    for item in panel.insights_planes[:3]:
        lineas.append(
            i18n.t("seguros.aprendizaje.plan_item").format(
                segmento=item.segmento,
                plan=item.plan_propuesto_id,
                metrica=_render_ratio(i18n, item.metrica_principal),
                muestra=item.tamano_muestra,
            )
        )
    return lineas


def _lineas_playbooks(i18n: I18nManager, panel: PanelAprendizajeComercialSeguro) -> list[str]:
    lineas = [i18n.t("seguros.aprendizaje.playbooks")]
    for item in panel.playbooks[:3]:
        lineas.append(
            i18n.t("seguros.aprendizaje.playbook_item").format(
                segmento=item.segmento_objetivo,
                plan=item.plan_sugerido,
                argumento=item.argumento_principal,
                objecion=item.objecion_a_vigilar,
                accion=item.siguiente_accion_sugerida,
                cautela=item.cautela_muestral,
            )
        )
    return lineas


def _render_ratio(i18n: I18nManager, ratio: float | None) -> str:
    if ratio is None:
        return i18n.t("seguros.ejecutivo.ratio_insuficiente")
    return f"{round(ratio * 100, 1)}%"


def construir_texto_valor_economico(i18n: I18nManager, resumen: ResumenEjecutivoSeguros) -> str:
    lineas = [i18n.t("seguros.ejecutivo.valor_titulo")]
    for item in resumen.prioridades_valor[:4]:
        lineas.append(
            i18n.t("seguros.ejecutivo.valor_prioridad_item").format(
                id_oportunidad=item.id_oportunidad,
                score=round(item.score_impacto * 100, 1),
                categoria=item.categoria_valor.value,
                accion=item.accion_sugerida,
            )
        )
    for campania in resumen.campanias_rentables[:2]:
        lineas.append(
            i18n.t("seguros.ejecutivo.valor_campania_item").format(
                nombre=campania.nombre,
                valor=campania.valor_total_estimado,
                categoria=campania.categoria.value,
                accion=campania.accion_sugerida,
            )
        )
    for segmento in resumen.segmentos_rentables[:2]:
        lineas.append(
            i18n.t("seguros.ejecutivo.valor_segmento_item").format(
                segmento=segmento.segmento,
                valor=segmento.valor_total_estimado,
                conversion=_render_ratio(i18n, segmento.conversion_aproximada),
                accion=segmento.accion_sugerida,
            )
        )
    for insight in resumen.insights_rentabilidad[:2]:
        lineas.append(
            i18n.t("seguros.ejecutivo.valor_insight_item").format(
                titulo=insight.titulo,
                valor=insight.valor_estimado,
                cautela=insight.nivel_cautela.value,
                accion=insight.accion_sugerida,
            )
        )
    if len(lineas) == 1:
        lineas.append(i18n.t("seguros.ejecutivo.valor_sin_dato"))
    return "\n".join(lineas)


def construir_texto_forecast(i18n: I18nManager, resumen: ResumenEjecutivoSeguros) -> str:
    forecast = resumen.forecast
    lineas = [
        i18n.t("seguros.ejecutivo.forecast_titulo"),
        i18n.t("seguros.ejecutivo.forecast_resumen").format(
            horizonte=forecast.horizonte.value,
            conversiones=forecast.conversiones_esperadas,
            renovaciones=forecast.renovaciones_salvables_esperadas,
            valor=forecast.valor_esperado,
            cautela=forecast.cautela.value,
            riesgo=forecast.riesgo_principal,
            accion=forecast.accion_sugerida,
        ),
    ]
    for item in resumen.escenarios[:3]:
        lineas.append(
            i18n.t("seguros.ejecutivo.forecast_escenario_item").format(
                estrategia=item.estrategia,
                poblacion=item.tamano_poblacion,
                conversion=_render_ratio(i18n, item.conversion_esperada),
                valor=item.valor_esperado,
                riesgo=item.riesgo_principal,
            )
        )
    for desvio in resumen.desvios_objetivo[:3]:
        lineas.append(
            i18n.t("seguros.ejecutivo.forecast_desvio_item").format(
                objetivo=desvio.objetivo.nombre,
                proyectado=desvio.valor_proyectado,
                objetivo_valor=desvio.objetivo.valor_objetivo,
                estado=desvio.estado.value,
                brecha=desvio.brecha,
            )
        )
    recomendacion = resumen.recomendacion_estrategica
    lineas.append(
        i18n.t("seguros.ejecutivo.forecast_recomendacion").format(
            foco=recomendacion.foco,
            accion=recomendacion.accion_sugerida,
            por_que=recomendacion.por_que,
            cautela=recomendacion.cautela.value,
        )
    )
    return "\n".join(lineas)
