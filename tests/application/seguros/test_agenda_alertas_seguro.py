from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from clinicdesk.app.application.seguros import AgendaAlertasSeguroService, EstadoObjetivoSeguro, EstadoTareaSeguro
from clinicdesk.app.application.seguros.analitica_ejecutiva import CampaniaAccionableSeguro, ResumenEjecutivoSeguros
from clinicdesk.app.application.seguros.forecast_contratos import (
    DesvioObjetivoSeguro,
    ForecastComercialSeguro,
    HorizonteForecastSeguro,
    NivelCautelaForecastSeguro,
    ObjetivoComercialSeguro,
    RecomendacionEstrategicaSeguro,
)
from clinicdesk.app.domain.seguros import (
    CampaniaSeguro,
    CriterioCampaniaSeguro,
    EstadoCampaniaSeguro,
    EstadoOperativoSeguro,
    ItemColaComercialSeguro,
    PrioridadTrabajoSeguro,
    RecordatorioSeguimientoSeguro,
    TipoItemColaSeguro,
    crear_resultado_vacio,
)
from clinicdesk.app.domain.seguros.campanias import OrigenCampaniaSeguro
from clinicdesk.app.domain.seguros.cola_operativa import ColaTrabajoSeguro


@dataclass
class _ColaFake:
    cola: ColaTrabajoSeguro

    def construir_cola_diaria(self, ahora=None) -> ColaTrabajoSeguro:  # noqa: ARG002
        return self.cola


@dataclass
class _AnaliticaFake:
    resumen: ResumenEjecutivoSeguros

    def construir_resumen(self) -> ResumenEjecutivoSeguros:
        return self.resumen


@dataclass
class _CampaniasFake:
    campanias: tuple[CampaniaSeguro, ...]

    def listar_campanias(self) -> tuple[CampaniaSeguro, ...]:
        return self.campanias


def _item(id_oportunidad: str, dias: int, estado: EstadoOperativoSeguro) -> ItemColaComercialSeguro:
    fecha = date(2026, 3, 10) + timedelta(days=dias)
    return ItemColaComercialSeguro(
        id_oportunidad=id_oportunidad,
        tipo_item=TipoItemColaSeguro.RENOVACION,
        prioridad=PrioridadTrabajoSeguro.MUY_PRIORITARIA,
        motivo_principal="riesgo alto",
        siguiente_accion_sugerida="contacto_hoy",
        estado_operativo=estado,
        riesgo_cautela="MEDIA",
        plan_contexto="origen -> destino",
        score_prioridad=0.9,
        recordatorio=RecordatorioSeguimientoSeguro(fecha_objetivo=fecha, vencido=dias <= 0, dias_desfase=max(-dias, 0)),
        ultima_gestion=None,
    )


def _resumen() -> ResumenEjecutivoSeguros:
    objetivo = ObjetivoComercialSeguro("conversiones", 12, "conteo", HorizonteForecastSeguro.DIAS_30)
    desvio = DesvioObjetivoSeguro(
        objetivo=objetivo,
        valor_proyectado=8,
        brecha=-4,
        estado=EstadoObjetivoSeguro.POR_DEBAJO,
        base_calculo="forecast",
        explicacion="brecha relevante",
    )
    campania = CampaniaAccionableSeguro(
        id_campania="sugerida-1",
        titulo="Reactivar cartera",
        criterio="fit",
        tamano_estimado=6,
        motivo="oportunidad",
        accion_recomendada="activar",
        cautela="media",
        ids_oportunidad=("opp-1",),
    )
    forecast = ForecastComercialSeguro(
        horizonte=HorizonteForecastSeguro.DIAS_30,
        base_calculo="base",
        conversiones_esperadas=5,
        renovaciones_salvables_esperadas=3,
        volumen_esperado=20,
        valor_esperado=1500.0,
        cautela=NivelCautelaForecastSeguro.MEDIA,
        riesgo_principal="desvio",
        accion_sugerida="plan",
        proyecciones_campania=(),
        proyecciones_cohorte=(),
    )
    recomendacion = RecomendacionEstrategicaSeguro(
        foco="retencion",
        base_calculo="forecast",
        valor_esperado=1200.0,
        volumen_esperado=10,
        cautela=NivelCautelaForecastSeguro.MEDIA,
        riesgo_principal="desvio",
        accion_sugerida="priorizar",
        por_que="brecha",
    )
    return ResumenEjecutivoSeguros(
        fecha_corte=date(2026, 3, 10),
        total_oportunidades=10,
        oportunidades_abiertas=5,
        convertidas=3,
        rechazadas=1,
        pospuestas=1,
        renovaciones_pendientes=2,
        renovaciones_en_riesgo=1,
        ratio_conversion_global=0.3,
        metrica_funnel=(),
        estado_embudo=(),
        cohortes=(),
        grupos_renovacion=(),
        campanias=(campania,),
        insights=(),
        prioridades_valor=(),
        campanias_rentables=(),
        segmentos_rentables=(),
        insights_rentabilidad=(),
        forecast=forecast,
        escenarios=(),
        desvios_objetivo=(desvio,),
        recomendacion_estrategica=recomendacion,
    )


def test_genera_alertas_y_tareas_vencidas_en_plan_semanal() -> None:
    cola = ColaTrabajoSeguro(
        fecha_corte=datetime(2026, 3, 10, tzinfo=UTC),
        items=(
            _item("opp-1", -2, EstadoOperativoSeguro.PENDIENTE),
            _item("opp-2", 3, EstadoOperativoSeguro.PENDIENTE),
        ),
    )
    campania = CampaniaSeguro(
        id_campania="camp-1",
        nombre="Campaña retención",
        objetivo_comercial="retener",
        creado_en=datetime(2026, 3, 1, tzinfo=UTC),
        criterio=CriterioCampaniaSeguro(OrigenCampaniaSeguro.SUGERENCIA, "fit", "sug"),
        tamano_lote=10,
        estado=EstadoCampaniaSeguro.EN_EJECUCION,
        resultado_agregado=crear_resultado_vacio(10),
    )
    servicio = AgendaAlertasSeguroService(_ColaFake(cola), _AnaliticaFake(_resumen()), _CampaniasFake((campania,)))

    plan = servicio.construir_plan_semanal(date(2026, 3, 10))

    assert plan.alertas_activas
    assert plan.agenda.tareas_vencidas
    assert any(alerta.tipo.value == "OBJETIVO_EN_RIESGO" for alerta in plan.alertas_activas)
    assert plan.acciones_rapidas


def test_actualizar_estado_tarea_agrega_traza() -> None:
    cola = ColaTrabajoSeguro(
        fecha_corte=datetime(2026, 3, 10, tzinfo=UTC),
        items=(_item("opp-1", 1, EstadoOperativoSeguro.PENDIENTE),),
    )
    servicio = AgendaAlertasSeguroService(_ColaFake(cola), _AnaliticaFake(_resumen()), _CampaniasFake(()))
    tarea = servicio.construir_plan_semanal(date(2026, 3, 10)).agenda.tareas_semana[0]

    actualizada = servicio.actualizar_estado_tarea(tarea, EstadoTareaSeguro.RESUELTA, "llamada completada")

    assert actualizada.estado is EstadoTareaSeguro.RESUELTA
    assert actualizada.traza[-1].comentario == "llamada completada"
