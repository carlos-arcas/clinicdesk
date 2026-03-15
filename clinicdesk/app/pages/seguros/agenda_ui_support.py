from __future__ import annotations

from clinicdesk.app.application.seguros import PlanSemanalSeguro, ResumenSemanaSeguro
from clinicdesk.app.i18n import I18nManager


def construir_texto_alertas_activas(i18n: I18nManager, plan: PlanSemanalSeguro) -> str:
    lineas = [i18n.t("seguros.agenda.alertas_titulo")]
    for alerta in plan.alertas_activas[:8]:
        lineas.append(
            i18n.t("seguros.agenda.alerta_item").format(
                tipo=alerta.tipo.value,
                prioridad=alerta.prioridad.value,
                motivo=alerta.motivo,
                accion=alerta.accion_sugerida,
            )
        )
    if len(lineas) == 1:
        lineas.append(i18n.t("seguros.agenda.sin_alertas"))
    return "\n".join(lineas)


def construir_texto_plan_semanal(i18n: I18nManager, plan: PlanSemanalSeguro) -> str:
    lineas = [i18n.t("seguros.agenda.plan_titulo")]
    for tarea in plan.agenda.tareas_semana[:10]:
        fecha = tarea.fecha_objetivo.isoformat() if tarea.fecha_objetivo else "-"
        lineas.append(
            i18n.t("seguros.agenda.tarea_item").format(
                prioridad=tarea.prioridad.value,
                estado=tarea.estado.value,
                fecha=fecha,
                accion=tarea.accion_sugerida,
                motivo=tarea.motivo,
            )
        )
    return "\n".join(lineas)


def construir_texto_tareas_vencidas(i18n: I18nManager, plan: PlanSemanalSeguro) -> str:
    vencidas = plan.agenda.tareas_vencidas
    if not vencidas:
        return i18n.t("seguros.agenda.sin_vencidas")
    lineas = [i18n.t("seguros.agenda.vencidas_titulo")]
    for tarea in vencidas[:6]:
        lineas.append(
            i18n.t("seguros.agenda.vencida_item").format(
                id_tarea=tarea.id_tarea,
                contexto=tarea.contexto,
                accion=tarea.accion_sugerida,
            )
        )
    return "\n".join(lineas)


def construir_texto_acciones_rapidas(i18n: I18nManager, plan: PlanSemanalSeguro) -> str:
    lineas = [i18n.t("seguros.agenda.acciones_titulo")]
    for accion in plan.acciones_rapidas[:4]:
        lineas.append(i18n.t("seguros.agenda.accion_item").format(accion=accion))
    return "\n".join(lineas)


def construir_texto_cierre_semanal(i18n: I18nManager, resumen: ResumenSemanaSeguro) -> str:
    cumplimiento = resumen.cumplimiento.porcentaje_cumplimiento
    lineas = [
        i18n.t("seguros.cierre.titulo"),
        i18n.t("seguros.cierre.resumen").format(
            inicio=resumen.cierre.periodo.fecha_inicio.isoformat(),
            fin=resumen.cierre.periodo.fecha_fin.isoformat(),
            cumplimiento=f"{cumplimiento:.1f}",
            ejecutadas=len(resumen.cierre.tareas_ejecutadas),
            previstas=len(resumen.cierre.tareas_previstas),
            pendientes=len(resumen.cierre.tareas_pendientes),
            vencidas=len(resumen.cierre.tareas_vencidas),
        ),
    ]
    for patron in resumen.cierre.patrones[:3]:
        lineas.append(i18n.t("seguros.cierre.patron_item").format(texto=patron))
    if not resumen.cierre.patrones:
        lineas.append(i18n.t("seguros.cierre.sin_patrones"))
    return "\n".join(lineas)


def construir_texto_bloqueos(i18n: I18nManager, resumen: ResumenSemanaSeguro) -> str:
    if not resumen.bloqueos:
        return i18n.t("seguros.cierre.sin_bloqueos")
    lineas = [i18n.t("seguros.cierre.bloqueos_titulo")]
    for bloqueo in resumen.bloqueos[:4]:
        lineas.append(
            i18n.t("seguros.cierre.bloqueo_item").format(
                codigo=bloqueo.codigo,
                descripcion=bloqueo.descripcion,
                accion=bloqueo.accion_desbloqueo,
            )
        )
    return "\n".join(lineas)


def construir_texto_recomendacion_cierre(i18n: I18nManager, resumen: ResumenSemanaSeguro) -> str:
    return i18n.t("seguros.cierre.recomendacion").format(texto=resumen.cierre.recomendacion_semana_siguiente)
