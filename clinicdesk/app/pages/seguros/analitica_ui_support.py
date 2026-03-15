from __future__ import annotations

from clinicdesk.app.application.seguros import ResumenEjecutivoSeguros
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


def _render_ratio(i18n: I18nManager, ratio: float | None) -> str:
    if ratio is None:
        return i18n.t("seguros.ejecutivo.ratio_insuficiente")
    return f"{round(ratio * 100, 1)}%"
