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
