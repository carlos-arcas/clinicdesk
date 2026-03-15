from __future__ import annotations

import logging
from dataclasses import replace
from datetime import UTC, date, datetime

from clinicdesk.app.application.seguros.agenda_alertas_contratos import (
    AgendaComercialSeguro,
    AlertaComercialSeguro,
    EstadoTareaSeguro,
    PlanSemanalSeguro,
    PrioridadAlertaSeguro,
    ReglaAlertaSeguro,
    RiesgoObjetivoSeguro,
    TareaComercialSeguro,
    TipoAlertaComercialSeguro,
    TrazaResolucionTareaSeguro,
)
from clinicdesk.app.application.seguros.analitica_ejecutiva import (
    AnaliticaEjecutivaSegurosService,
    ResumenEjecutivoSeguros,
)
from clinicdesk.app.application.seguros.campanias import GestionCampaniasSeguroService
from clinicdesk.app.application.seguros.seguridad_observabilidad import construir_evento_log_seguro
from clinicdesk.app.application.seguros.cola_trabajo import ColaTrabajoSeguroService
from clinicdesk.app.domain.seguros import EstadoCampaniaSeguro, EstadoOperativoSeguro, PrioridadTrabajoSeguro

LOGGER = logging.getLogger(__name__)

_MAPA_PRIORIDAD = {
    PrioridadTrabajoSeguro.MUY_PRIORITARIA: PrioridadAlertaSeguro.CRITICA,
    PrioridadTrabajoSeguro.PRIORITARIA: PrioridadAlertaSeguro.ALTA,
    PrioridadTrabajoSeguro.SECUNDARIA: PrioridadAlertaSeguro.MEDIA,
    PrioridadTrabajoSeguro.NO_PRIORITARIA: PrioridadAlertaSeguro.MEDIA,
}

_MAPA_ESTADO = {
    EstadoOperativoSeguro.PENDIENTE: EstadoTareaSeguro.PENDIENTE,
    EstadoOperativoSeguro.EN_CURSO: EstadoTareaSeguro.EN_CURSO,
    EstadoOperativoSeguro.POSPUESTO: EstadoTareaSeguro.POSPUESTA,
    EstadoOperativoSeguro.PENDIENTE_DOCUMENTACION: EstadoTareaSeguro.PENDIENTE,
    EstadoOperativoSeguro.RESUELTO: EstadoTareaSeguro.RESUELTA,
    EstadoOperativoSeguro.DESCARTADO: EstadoTareaSeguro.DESCARTADA,
}


class AgendaAlertasSeguroService:
    def __init__(
        self,
        cola: ColaTrabajoSeguroService,
        analitica: AnaliticaEjecutivaSegurosService,
        campanias: GestionCampaniasSeguroService,
    ) -> None:
        self._cola = cola
        self._analitica = analitica
        self._campanias = campanias

    def construir_plan_semanal(self, fecha: date | None = None) -> PlanSemanalSeguro:
        ahora = datetime.now(UTC)
        fecha_corte = fecha or ahora.date()
        cola = self._cola.construir_cola_diaria(ahora)
        resumen = self._analitica.construir_resumen()
        alertas = self._construir_alertas(resumen, fecha_corte)
        tareas = self._construir_tareas(cola.items, alertas, fecha_corte)
        agenda = AgendaComercialSeguro(
            fecha_corte=fecha_corte,
            prioridades_hoy=tuple(
                t for t in tareas if t.prioridad in {PrioridadAlertaSeguro.CRITICA, PrioridadAlertaSeguro.ALTA}
            )[:8],
            tareas_vencidas=tuple(t for t in tareas if t.estado is EstadoTareaSeguro.VENCIDA),
            tareas_semana=tareas[:16],
        )
        riesgos = self._riesgos_objetivo(resumen)
        acciones = _acciones_rapidas(agenda, alertas, riesgos)
        LOGGER.info(
            "plan_semanal_seguro_generado",
            extra=construir_evento_log_seguro(
                "logging_tecnico_seguro",
                "plan_semanal_seguro_generado",
                {
                    "correlation_id": fecha_corte.isoformat(),
                    "alertas": len(alertas),
                    "tareas": len(tareas),
                    "outcome": "ok",
                },
            ),
        )
        return PlanSemanalSeguro(
            agenda=agenda, alertas_activas=alertas, riesgos_objetivo=riesgos, acciones_rapidas=acciones
        )

    def actualizar_estado_tarea(
        self,
        tarea: TareaComercialSeguro,
        nuevo_estado: EstadoTareaSeguro,
        comentario: str,
        fecha: datetime | None = None,
    ) -> TareaComercialSeguro:
        traza = TrazaResolucionTareaSeguro(
            fecha=fecha or datetime.now(UTC),
            estado_anterior=tarea.estado,
            estado_nuevo=nuevo_estado,
            comentario=comentario.strip() or "actualizacion_operativa",
        )
        return replace(tarea, estado=nuevo_estado, traza=tarea.traza + (traza,))

    def _construir_alertas(
        self, resumen: ResumenEjecutivoSeguros, fecha_corte: date
    ) -> tuple[AlertaComercialSeguro, ...]:
        alertas: list[AlertaComercialSeguro] = []
        cola = self._cola.construir_cola_diaria(datetime.combine(fecha_corte, datetime.min.time(), tzinfo=UTC))
        campanias = {camp.nombre.lower(): camp for camp in self._campanias.listar_campanias()}
        for renovacion in cola.filtrar_vencidas():
            dias = renovacion.recordatorio.dias_desfase if renovacion.recordatorio else 0
            alertas.append(
                AlertaComercialSeguro(
                    id_alerta=f"ren-vencida-{renovacion.id_oportunidad}",
                    tipo=TipoAlertaComercialSeguro.RENOVACION_VENCIDA,
                    prioridad=PrioridadAlertaSeguro.CRITICA,
                    regla=ReglaAlertaSeguro.RENOVACION_VENCIDA_SIN_GESTION,
                    motivo=f"Renovación vencida con desfase de {dias} días.",
                    accion_sugerida="Contactar hoy y escalar retención",
                    fecha_objetivo=renovacion.recordatorio.fecha_objetivo if renovacion.recordatorio else fecha_corte,
                    contexto=renovacion.plan_contexto,
                    id_oportunidad=renovacion.id_oportunidad,
                )
            )
        for item in cola.filtrar_renovaciones():
            if not item.recordatorio:
                continue
            dias_restantes = (item.recordatorio.fecha_objetivo - fecha_corte).days
            if 0 <= dias_restantes <= 7:
                alertas.append(
                    AlertaComercialSeguro(
                        id_alerta=f"ren-proxima-{item.id_oportunidad}",
                        tipo=TipoAlertaComercialSeguro.RENOVACION_PROXIMA,
                        prioridad=PrioridadAlertaSeguro.ALTA,
                        regla=ReglaAlertaSeguro.RENOVACION_MENOR_7_DIAS,
                        motivo=f"Renovación en {dias_restantes} días.",
                        accion_sugerida="Preparar propuesta de retención esta semana",
                        fecha_objetivo=item.recordatorio.fecha_objetivo,
                        contexto=item.plan_contexto,
                        id_oportunidad=item.id_oportunidad,
                    )
                )
        for item in cola.filtrar_alta_prioridad():
            if item.estado_operativo is not EstadoOperativoSeguro.PENDIENTE:
                continue
            alertas.append(
                AlertaComercialSeguro(
                    id_alerta=f"hot-{item.id_oportunidad}",
                    tipo=TipoAlertaComercialSeguro.OPORTUNIDAD_CALIENTE_SIN_TOQUE,
                    prioridad=PrioridadAlertaSeguro.ALTA,
                    regla=ReglaAlertaSeguro.OPORTUNIDAD_ALTA_PRIORIDAD_PENDIENTE,
                    motivo="Oportunidad de alta prioridad sin gestión operativa reciente.",
                    accion_sugerida="Ejecutar contacto inicial hoy",
                    fecha_objetivo=fecha_corte,
                    contexto=item.plan_contexto,
                    id_oportunidad=item.id_oportunidad,
                )
            )
        for desvio in resumen.desvios_objetivo:
            if desvio.estado.value != "POR_DEBAJO":
                continue
            alertas.append(
                AlertaComercialSeguro(
                    id_alerta=f"obj-{desvio.objetivo.nombre}",
                    tipo=TipoAlertaComercialSeguro.OBJETIVO_EN_RIESGO,
                    prioridad=PrioridadAlertaSeguro.CRITICA,
                    regla=ReglaAlertaSeguro.DESVIO_OBJETIVO_RELEVANTE,
                    motivo=f"Objetivo {desvio.objetivo.nombre} en desvío {desvio.brecha}.",
                    accion_sugerida="Reasignar foco semanal y revisar campañas",
                    fecha_objetivo=fecha_corte,
                    contexto=desvio.objetivo.nombre,
                )
            )
        for campania in self._campanias.listar_campanias():
            if campania.estado is not EstadoCampaniaSeguro.EN_EJECUCION:
                continue
            if campania.resultado_agregado.trabajados > 0:
                continue
            alertas.append(
                AlertaComercialSeguro(
                    id_alerta=f"camp-sin-avance-{campania.id_campania}",
                    tipo=TipoAlertaComercialSeguro.CAMPANIA_SIN_AVANCE,
                    prioridad=PrioridadAlertaSeguro.ALTA,
                    regla=ReglaAlertaSeguro.CAMPANIA_EN_EJECUCION_SIN_AVANCE,
                    motivo=f"Campaña {campania.nombre} activa sin avances registrados.",
                    accion_sugerida="Asignar responsable y primer lote hoy",
                    fecha_objetivo=fecha_corte,
                    contexto=campania.nombre,
                )
            )
        for sugerida in resumen.campanias[:2]:
            if sugerida.titulo.lower() in campanias:
                continue
            alertas.append(
                AlertaComercialSeguro(
                    id_alerta=f"sugerida-{sugerida.id_campania}",
                    tipo=TipoAlertaComercialSeguro.CAMPANIA_RECOMENDADA_NO_LANZADA,
                    prioridad=PrioridadAlertaSeguro.MEDIA,
                    regla=ReglaAlertaSeguro.SUGERENCIA_CAMPANIA_NO_EJECUTADA,
                    motivo=f"Sugerencia comercial {sugerida.titulo} aún no se lanzó.",
                    accion_sugerida="Crear campaña ejecutable desde sugerencia",
                    fecha_objetivo=fecha_corte,
                    contexto=sugerida.criterio,
                )
            )
        return tuple(_deduplicar_alertas(alertas))

    def _construir_tareas(
        self, items_cola, alertas: tuple[AlertaComercialSeguro, ...], fecha_corte: date
    ) -> tuple[TareaComercialSeguro, ...]:
        tareas: list[TareaComercialSeguro] = []
        for item in items_cola:
            estado = _MAPA_ESTADO[item.estado_operativo]
            if (
                item.recordatorio
                and item.recordatorio.vencido
                and estado in {EstadoTareaSeguro.PENDIENTE, EstadoTareaSeguro.EN_CURSO}
            ):
                estado = EstadoTareaSeguro.VENCIDA
            tareas.append(
                TareaComercialSeguro(
                    id_tarea=f"cola-{item.id_oportunidad}",
                    tipo=item.tipo_item.value,
                    prioridad=_MAPA_PRIORIDAD[item.prioridad],
                    motivo=item.motivo_principal,
                    accion_sugerida=item.siguiente_accion_sugerida,
                    fecha_objetivo=item.recordatorio.fecha_objetivo if item.recordatorio else fecha_corte,
                    contexto=item.plan_contexto,
                    estado=estado,
                    id_oportunidad=item.id_oportunidad,
                )
            )
        for alerta in alertas:
            tareas.append(
                TareaComercialSeguro(
                    id_tarea=f"alerta-{alerta.id_alerta}",
                    tipo=alerta.tipo.value,
                    prioridad=alerta.prioridad,
                    motivo=alerta.motivo,
                    accion_sugerida=alerta.accion_sugerida,
                    fecha_objetivo=alerta.fecha_objetivo,
                    contexto=alerta.contexto,
                    estado=EstadoTareaSeguro.PENDIENTE,
                    id_oportunidad=alerta.id_oportunidad,
                    es_alerta_informativa=True,
                )
            )
        return tuple(sorted(tareas, key=_clave_tarea))

    def _riesgos_objetivo(self, resumen: ResumenEjecutivoSeguros) -> tuple[RiesgoObjetivoSeguro, ...]:
        riesgos = [
            RiesgoObjetivoSeguro(
                nombre_objetivo=item.objetivo.nombre,
                valor_objetivo=item.objetivo.valor_objetivo,
                valor_proyectado=item.valor_proyectado,
                brecha=item.brecha,
                estado=item.estado.value,
            )
            for item in resumen.desvios_objetivo
            if item.estado.value == "POR_DEBAJO"
        ]
        return tuple(riesgos)


def _deduplicar_alertas(alertas: list[AlertaComercialSeguro]) -> list[AlertaComercialSeguro]:
    vistos: set[str] = set()
    resultado: list[AlertaComercialSeguro] = []
    for alerta in sorted(alertas, key=lambda item: item.id_alerta):
        if alerta.id_alerta in vistos:
            continue
        vistos.add(alerta.id_alerta)
        resultado.append(alerta)
    return resultado


def _clave_tarea(tarea: TareaComercialSeguro) -> tuple[int, date, str]:
    prioridad = {
        PrioridadAlertaSeguro.CRITICA: 0,
        PrioridadAlertaSeguro.ALTA: 1,
        PrioridadAlertaSeguro.MEDIA: 2,
    }[tarea.prioridad]
    return prioridad, tarea.fecha_objetivo or date.max, tarea.id_tarea


def _acciones_rapidas(
    agenda: AgendaComercialSeguro,
    alertas: tuple[AlertaComercialSeguro, ...],
    riesgos: tuple[RiesgoObjetivoSeguro, ...],
) -> tuple[str, ...]:
    acciones: list[str] = []
    if agenda.tareas_vencidas:
        acciones.append("Resolver primero tareas vencidas de renovación")
    if any(item.tipo is TipoAlertaComercialSeguro.OBJETIVO_EN_RIESGO for item in alertas):
        acciones.append("Replanificar foco semanal para objetivos en riesgo")
    if any(item.tipo is TipoAlertaComercialSeguro.CAMPANIA_SIN_AVANCE for item in alertas):
        acciones.append("Activar campaña en ejecución sin avance con lote mínimo")
    if riesgos and not acciones:
        acciones.append("Revisar brechas de forecast y ajustar agenda comercial")
    if not acciones:
        acciones.append("Mantener ritmo operativo de seguimiento y renovaciones")
    return tuple(acciones)
