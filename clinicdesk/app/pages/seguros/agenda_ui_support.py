from __future__ import annotations

from clinicdesk.app.application.seguros import PlanSemanalSeguro
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
