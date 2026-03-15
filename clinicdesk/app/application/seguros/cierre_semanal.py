from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from clinicdesk.app.application.seguros.agenda_alertas import AgendaAlertasSeguroService
from clinicdesk.app.application.seguros.agenda_alertas_contratos import EstadoTareaSeguro, TareaComercialSeguro
from clinicdesk.app.application.seguros.analitica_ejecutiva import AnaliticaEjecutivaSegurosService
from clinicdesk.app.application.seguros.campanias import GestionCampaniasSeguroService
from clinicdesk.app.application.seguros.cierre_semanal_contratos import (
    AprendizajeEjecucionSeguro,
    BloqueoOperativoSeguro,
    CierreSemanalSeguro,
    CumplimientoPlanSeguro,
    DesvioEjecucionSeguro,
    PeriodoSemanaSeguro,
    ResumenSemanaSeguro,
)
from clinicdesk.app.application.seguros.cola_trabajo import ColaTrabajoSeguroService
from clinicdesk.app.application.seguros.comercial import RepositorioComercialSeguro
from clinicdesk.app.domain.seguros import AccionPendienteSeguro, EstadoOperativoSeguro, TipoItemColaSeguro


@dataclass(frozen=True, slots=True)
class _PatronOperativoSeguro:
    posposiciones_recurrentes: tuple[str, ...]
    campanias_no_lanzadas: tuple[str, ...]
    renovaciones_criticas_no_atendidas: int


class CierreSemanalSeguroService:
    def __init__(
        self,
        agenda: AgendaAlertasSeguroService,
        cola: ColaTrabajoSeguroService,
        analitica: AnaliticaEjecutivaSegurosService,
        campanias: GestionCampaniasSeguroService,
        repositorio: RepositorioComercialSeguro,
    ) -> None:
        self._agenda = agenda
        self._cola = cola
        self._analitica = analitica
        self._campanias = campanias
        self._repositorio = repositorio

    def construir_resumen_semana(self, fecha_corte: date | None = None) -> ResumenSemanaSeguro:
        ahora = fecha_corte or datetime.now(UTC).date()
        periodo = _periodo_semana(ahora)
        plan = self._agenda.construir_plan_semanal(ahora)
        tareas_previstas = plan.agenda.tareas_semana
        tareas_ejecutadas = tuple(t for t in tareas_previstas if t.estado in _ESTADOS_EJECUTADOS)
        tareas_pendientes = tuple(t for t in tareas_previstas if t.estado in _ESTADOS_PENDIENTES)
        tareas_vencidas = plan.agenda.tareas_vencidas
        tareas_criticas_no_ejecutadas = tuple(
            tarea
            for tarea in tareas_previstas
            if tarea.prioridad.value in {"CRITICA", "ALTA"} and tarea.estado not in _ESTADOS_EJECUTADOS
        )
        cumplimiento = _calcular_cumplimiento(
            periodo,
            tareas_previstas,
            tareas_ejecutadas,
            tareas_pendientes,
            tareas_vencidas,
            tareas_criticas_no_ejecutadas,
        )
        patrones = self._detectar_patrones(periodo)
        desvios = _construir_desvios(
            cumplimiento, patrones, len(tareas_vencidas), len(tareas_pendientes), len(tareas_ejecutadas)
        )
        bloqueos = _bloqueos_desde_desvios(periodo, desvios)
        recomendacion = _recomendacion_foco(cumplimiento, patrones, bloqueos)
        cierre = CierreSemanalSeguro(
            periodo=periodo,
            tareas_previstas=tareas_previstas,
            tareas_ejecutadas=tareas_ejecutadas,
            tareas_pendientes=tareas_pendientes,
            tareas_vencidas=tareas_vencidas,
            bloqueos=bloqueos,
            patrones=_resumen_patrones(patrones),
            recomendacion_semana_siguiente=recomendacion,
        )
        aprendizaje = _construir_aprendizaje(
            periodo, tareas_ejecutadas, tareas_pendientes, bloqueo_descripciones=bloqueos
        )
        return ResumenSemanaSeguro(
            cierre=cierre,
            cumplimiento=cumplimiento,
            desvios=desvios,
            bloqueos=bloqueos,
            aprendizaje=aprendizaje,
        )

    def _detectar_patrones(self, periodo: PeriodoSemanaSeguro) -> _PatronOperativoSeguro:
        cola = self._cola.construir_cola_diaria(datetime.combine(periodo.fecha_corte, datetime.min.time(), tzinfo=UTC))
        oportunidades = [item.id_oportunidad for item in cola.items]
        posposiciones = tuple(
            item
            for item in oportunidades
            if _contar_posposiciones(self._repositorio.listar_gestiones_operativas(item, limite=8)) >= 2
        )
        campanias_actuales = {item.nombre.lower() for item in self._campanias.listar_campanias()}
        sugeridas = self._analitica.construir_resumen().campanias
        no_lanzadas = tuple(c.titulo for c in sugeridas if c.titulo.lower() not in campanias_actuales)
        renovaciones_no_atendidas = sum(
            1
            for item in cola.items
            if item.tipo_item is TipoItemColaSeguro.RENOVACION
            and item.prioridad.value in {"MUY_PRIORITARIA", "PRIORITARIA"}
            and item.estado_operativo is not EstadoOperativoSeguro.RESUELTO
        )
        return _PatronOperativoSeguro(posposiciones, no_lanzadas, renovaciones_no_atendidas)


def _periodo_semana(fecha_corte: date) -> PeriodoSemanaSeguro:
    inicio = fecha_corte - timedelta(days=fecha_corte.weekday())
    return PeriodoSemanaSeguro(fecha_inicio=inicio, fecha_fin=inicio + timedelta(days=6), fecha_corte=fecha_corte)


def _calcular_cumplimiento(
    periodo: PeriodoSemanaSeguro,
    tareas_previstas: tuple[TareaComercialSeguro, ...],
    tareas_ejecutadas: tuple[TareaComercialSeguro, ...],
    tareas_pendientes: tuple[TareaComercialSeguro, ...],
    tareas_vencidas: tuple[TareaComercialSeguro, ...],
    tareas_criticas_no_ejecutadas: tuple[TareaComercialSeguro, ...],
) -> CumplimientoPlanSeguro:
    total = len(tareas_previstas)
    porcentaje = round((len(tareas_ejecutadas) / total) * 100, 2) if total else 0.0
    return CumplimientoPlanSeguro(
        periodo=periodo,
        tareas_previstas=tareas_previstas,
        tareas_ejecutadas=tareas_ejecutadas,
        tareas_pendientes=tareas_pendientes,
        tareas_vencidas=tareas_vencidas,
        tareas_criticas_no_ejecutadas=tareas_criticas_no_ejecutadas,
        porcentaje_cumplimiento=porcentaje,
    )


def _construir_desvios(
    cumplimiento: CumplimientoPlanSeguro,
    patrones: _PatronOperativoSeguro,
    total_vencidas: int,
    total_pendientes: int,
    total_ejecutadas: int,
) -> tuple[DesvioEjecucionSeguro, ...]:
    desvios: list[DesvioEjecucionSeguro] = []
    periodo = cumplimiento.periodo
    if cumplimiento.porcentaje_cumplimiento < 60:
        desvios.append(
            DesvioEjecucionSeguro(
                periodo=periodo,
                codigo="CUMPLIMIENTO_BAJO",
                severidad="ALTA",
                descripcion="Cumplimiento semanal por debajo de 60%.",
                impacto="Riesgo de no cerrar objetivos comerciales del periodo.",
                accion_recomendada="Reducir alcance y cerrar primero tareas críticas pendientes.",
            )
        )
    if total_vencidas >= 3:
        desvios.append(
            DesvioEjecucionSeguro(
                periodo=periodo,
                codigo="VENCIDAS_RECURRENTES",
                severidad="ALTA",
                descripcion="Demasiadas tareas vencidas acumuladas en la semana.",
                impacto="Aumenta desfase operativo y deteriora renovaciones.",
                accion_recomendada="Reservar bloque diario exclusivo para vencidas.",
            )
        )
    if patrones.posposiciones_recurrentes:
        desvios.append(
            DesvioEjecucionSeguro(
                periodo=periodo,
                codigo="POSPOSICION_REPETIDA",
                severidad="MEDIA",
                descripcion="Hay oportunidades pospuestas repetidamente.",
                impacto="Se cronifica el backlog en casos sensibles.",
                accion_recomendada="Escalar las oportunidades más postergadas con dueño explícito.",
            )
        )
    if patrones.campanias_no_lanzadas:
        desvios.append(
            DesvioEjecucionSeguro(
                periodo=periodo,
                codigo="CAMPANIA_NO_EJECUTADA",
                severidad="MEDIA",
                descripcion="Campañas sugeridas no lanzadas en la misma semana.",
                impacto="Se pierde tracción sobre segmentos con señal de avance.",
                accion_recomendada="Lanzar un lote mínimo de campaña antes de abrir nuevas líneas.",
            )
        )
    if patrones.renovaciones_criticas_no_atendidas > 0:
        desvios.append(
            DesvioEjecucionSeguro(
                periodo=periodo,
                codigo="RENOVACION_CRITICA_PENDIENTE",
                severidad="ALTA",
                descripcion="Persisten renovaciones críticas sin atención resolutiva.",
                impacto="Eleva riesgo de fuga de cartera y caída de conversión.",
                accion_recomendada="Priorizar renovaciones críticas en la primera franja del día.",
            )
        )
    if total_pendientes > total_ejecutadas:
        desvios.append(
            DesvioEjecucionSeguro(
                periodo=periodo,
                codigo="PENDIENTE_SUPERA_RESUELTO",
                severidad="MEDIA",
                descripcion="El volumen pendiente supera lo ejecutado.",
                impacto="La operación absorbe capacidad y reduce cierre efectivo.",
                accion_recomendada="Limitar nuevas entradas hasta recuperar ratio de cierre.",
            )
        )
    return tuple(desvios)


def _bloqueos_desde_desvios(
    periodo: PeriodoSemanaSeguro, desvios: tuple[DesvioEjecucionSeguro, ...]
) -> tuple[BloqueoOperativoSeguro, ...]:
    return tuple(
        BloqueoOperativoSeguro(
            periodo=periodo,
            codigo=f"BLQ-{desvio.codigo}",
            descripcion=desvio.descripcion,
            evidencia=desvio.impacto,
            accion_desbloqueo=desvio.accion_recomendada,
        )
        for desvio in desvios
        if desvio.severidad in {"ALTA", "MEDIA"}
    )


def _construir_aprendizaje(
    periodo: PeriodoSemanaSeguro,
    tareas_ejecutadas: tuple[TareaComercialSeguro, ...],
    tareas_pendientes: tuple[TareaComercialSeguro, ...],
    bloqueo_descripciones: tuple[BloqueoOperativoSeguro, ...],
) -> AprendizajeEjecucionSeguro:
    tipos_ejecutados = _top_tipos(tareas_ejecutadas)
    tipos_pendientes = _top_tipos(tareas_pendientes)
    acciones = _top_acciones(tareas_ejecutadas)
    zonas_atasco = tuple(b.descripcion for b in bloqueo_descripciones[:3])
    recomendacion = _recomendacion_aprendizaje(tipos_ejecutados, tipos_pendientes, zonas_atasco)
    return AprendizajeEjecucionSeguro(
        periodo=periodo,
        tareas_que_avanzan=tipos_ejecutados,
        tareas_que_se_atrasan=tipos_pendientes,
        acciones_con_mayor_avance=acciones,
        zonas_atasco=zonas_atasco,
        recomendacion_semana_siguiente=recomendacion,
    )


def _top_tipos(tareas: tuple[TareaComercialSeguro, ...]) -> tuple[str, ...]:
    conteo = Counter(item.tipo for item in tareas)
    return tuple(tipo for tipo, _ in conteo.most_common(3))


def _top_acciones(tareas: tuple[TareaComercialSeguro, ...]) -> tuple[str, ...]:
    conteo = Counter(item.accion_sugerida for item in tareas if item.accion_sugerida)
    return tuple(accion for accion, _ in conteo.most_common(3))


def _recomendacion_aprendizaje(
    tipos_ejecutados: tuple[str, ...], tipos_pendientes: tuple[str, ...], zonas_atasco: tuple[str, ...]
) -> str:
    if not tipos_ejecutados and tipos_pendientes:
        return "Se recomienda reducir alcance y consolidar ejecución antes de abrir nuevas iniciativas."
    if tipos_pendientes and tipos_ejecutados and tipos_pendientes[0] != tipos_ejecutados[0]:
        return (
            "Se observa desalineación entre lo planificado y lo ejecutado; conviene priorizar las tareas "
            f"{tipos_pendientes[0]} al inicio de semana."
        )
    if zonas_atasco:
        return "Persisten atascos operativos; mantener foco en desbloqueos críticos antes de expandir campañas."
    return "La ejecución semanal se mantiene estable; sostener foco y revisar capacidad antes de ampliar volumen."


def _recomendacion_foco(
    cumplimiento: CumplimientoPlanSeguro,
    patrones: _PatronOperativoSeguro,
    bloqueos: tuple[BloqueoOperativoSeguro, ...],
) -> str:
    if patrones.renovaciones_criticas_no_atendidas > 0:
        return "Priorizar renovaciones críticas y limitar campañas simultáneas hasta recuperar tracción."
    if patrones.campanias_no_lanzadas:
        return "Concentrar la semana en ejecutar una campaña sugerida con lote acotado y medible."
    if cumplimiento.porcentaje_cumplimiento < 70 or bloqueos:
        return "Reducir foco operativo a tareas de mayor impacto y cerrar vencidas antes de agregar carga."
    return "Mantener ritmo de ejecución y reforzar seguimiento de oportunidades de alto valor."


def _resumen_patrones(patrones: _PatronOperativoSeguro) -> tuple[str, ...]:
    resumen: list[str] = []
    if patrones.posposiciones_recurrentes:
        resumen.append(f"Posposición repetida en {len(patrones.posposiciones_recurrentes)} oportunidades")
    if patrones.campanias_no_lanzadas:
        resumen.append(f"{len(patrones.campanias_no_lanzadas)} campañas sugeridas sin lanzamiento")
    if patrones.renovaciones_criticas_no_atendidas:
        resumen.append(f"{patrones.renovaciones_criticas_no_atendidas} renovaciones críticas no atendidas")
    return tuple(resumen)


def _contar_posposiciones(gestiones) -> int:
    return sum(1 for gestion in gestiones if gestion.accion is AccionPendienteSeguro.POSPUESTO)


_ESTADOS_EJECUTADOS = {EstadoTareaSeguro.RESUELTA, EstadoTareaSeguro.DESCARTADA}
_ESTADOS_PENDIENTES = {
    EstadoTareaSeguro.PENDIENTE,
    EstadoTareaSeguro.EN_CURSO,
    EstadoTareaSeguro.POSPUESTA,
    EstadoTareaSeguro.VENCIDA,
}
