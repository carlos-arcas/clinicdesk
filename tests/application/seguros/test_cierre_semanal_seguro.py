from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from clinicdesk.app.application.seguros import (
    AgendaComercialSeguro,
    CierreSemanalSeguroService,
    EstadoObjetivoSeguro,
    EstadoTareaSeguro,
    PlanSemanalSeguro,
    PrioridadAlertaSeguro,
    RiesgoObjetivoSeguro,
    TareaComercialSeguro,
)
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
    AccionPendienteSeguro,
    CampaniaSeguro,
    CriterioCampaniaSeguro,
    EstadoCampaniaSeguro,
    EstadoOperativoSeguro,
    GestionOperativaColaSeguro,
    ItemColaComercialSeguro,
    PrioridadTrabajoSeguro,
    RecordatorioSeguimientoSeguro,
    TipoItemColaSeguro,
    crear_resultado_vacio,
)
from clinicdesk.app.domain.seguros.campanias import OrigenCampaniaSeguro
from clinicdesk.app.domain.seguros.cola_operativa import ColaTrabajoSeguro


@dataclass
class _AgendaFake:
    plan: PlanSemanalSeguro

    def construir_plan_semanal(self, fecha=None) -> PlanSemanalSeguro:  # noqa: ARG002
        return self.plan


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


@dataclass
class _RepositorioFake:
    gestiones: dict[str, tuple[GestionOperativaColaSeguro, ...]]

    def listar_gestiones_operativas(self, id_oportunidad: str, limite: int = 8):  # noqa: ARG002
        return self.gestiones.get(id_oportunidad, ())


def _tarea(id_tarea: str, prioridad: PrioridadAlertaSeguro, estado: EstadoTareaSeguro) -> TareaComercialSeguro:
    return TareaComercialSeguro(
        id_tarea=id_tarea,
        tipo="RENOVACION",
        prioridad=prioridad,
        motivo="riesgo",
        accion_sugerida="contacto_hoy",
        fecha_objetivo=date(2026, 3, 12),
        contexto="base",
        estado=estado,
    )


def _resumen() -> ResumenEjecutivoSeguros:
    objetivo = ObjetivoComercialSeguro("conversiones", 12, "conteo", HorizonteForecastSeguro.DIAS_30)
    desvio = DesvioObjetivoSeguro(
        objetivo=objetivo,
        valor_proyectado=8,
        brecha=-4,
        estado=EstadoObjetivoSeguro.POR_DEBAJO,
        base_calculo="forecast",
        explicacion="brecha",
    )
    campania = CampaniaAccionableSeguro(
        id_campania="sugerida-1",
        titulo="Reactivar cartera",
        criterio="fit",
        tamano_estimado=4,
        motivo="oportunidad",
        accion_recomendada="activar",
        cautela="media",
        ids_oportunidad=("opp-1",),
    )
    forecast = ForecastComercialSeguro(
        horizonte=HorizonteForecastSeguro.DIAS_30,
        base_calculo="base",
        conversiones_esperadas=4,
        renovaciones_salvables_esperadas=2,
        volumen_esperado=10,
        valor_esperado=1200.0,
        cautela=NivelCautelaForecastSeguro.MEDIA,
        riesgo_principal="desvio",
        accion_sugerida="ajustar",
        proyecciones_campania=(),
        proyecciones_cohorte=(),
    )
    recomendacion = RecomendacionEstrategicaSeguro(
        foco="retencion",
        base_calculo="forecast",
        valor_esperado=1000.0,
        volumen_esperado=10,
        cautela=NivelCautelaForecastSeguro.MEDIA,
        riesgo_principal="desvio",
        accion_sugerida="priorizar",
        por_que="brecha",
    )
    return ResumenEjecutivoSeguros(
        fecha_corte=date(2026, 3, 14),
        total_oportunidades=8,
        oportunidades_abiertas=5,
        convertidas=2,
        rechazadas=1,
        pospuestas=1,
        renovaciones_pendientes=2,
        renovaciones_en_riesgo=1,
        ratio_conversion_global=0.25,
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


def test_cierre_semanal_detecta_desvios_bloqueos_y_aprendizaje() -> None:
    tareas = (
        _tarea("t1", PrioridadAlertaSeguro.CRITICA, EstadoTareaSeguro.PENDIENTE),
        _tarea("t2", PrioridadAlertaSeguro.ALTA, EstadoTareaSeguro.VENCIDA),
        _tarea("t3", PrioridadAlertaSeguro.MEDIA, EstadoTareaSeguro.RESUELTA),
    )
    plan = PlanSemanalSeguro(
        agenda=AgendaComercialSeguro(
            fecha_corte=date(2026, 3, 14),
            prioridades_hoy=tareas[:2],
            tareas_vencidas=(tareas[1],),
            tareas_semana=tareas,
        ),
        alertas_activas=(),
        riesgos_objetivo=(RiesgoObjetivoSeguro("conv", 12, 8, -4, "POR_DEBAJO"),),
        acciones_rapidas=("resolver",),
    )
    cola = ColaTrabajoSeguro(
        fecha_corte=datetime(2026, 3, 14, tzinfo=UTC),
        items=(
            ItemColaComercialSeguro(
                id_oportunidad="opp-1",
                tipo_item=TipoItemColaSeguro.RENOVACION,
                prioridad=PrioridadTrabajoSeguro.MUY_PRIORITARIA,
                motivo_principal="alto",
                siguiente_accion_sugerida="contacto_hoy",
                estado_operativo=EstadoOperativoSeguro.PENDIENTE,
                riesgo_cautela="MEDIA",
                plan_contexto="a",
                score_prioridad=0.9,
                recordatorio=RecordatorioSeguimientoSeguro(date(2026, 3, 13), True, 1),
                ultima_gestion=None,
            ),
        ),
    )
    campania = CampaniaSeguro(
        id_campania="camp-1",
        nombre="Campaña activa distinta",
        objetivo_comercial="retener",
        creado_en=datetime(2026, 3, 1, tzinfo=UTC),
        criterio=CriterioCampaniaSeguro(OrigenCampaniaSeguro.SUGERENCIA, "fit", "ref"),
        tamano_lote=2,
        estado=EstadoCampaniaSeguro.CREADA,
        resultado_agregado=crear_resultado_vacio(2),
    )
    repo = _RepositorioFake(
        gestiones={
            "opp-1": (
                GestionOperativaColaSeguro(
                    id_oportunidad="opp-1",
                    accion=AccionPendienteSeguro.POSPUESTO,
                    estado_resultante=EstadoOperativoSeguro.POSPUESTO,
                    nota_corta="x",
                    siguiente_paso="x",
                    timestamp=datetime(2026, 3, 12, tzinfo=UTC),
                ),
                GestionOperativaColaSeguro(
                    id_oportunidad="opp-1",
                    accion=AccionPendienteSeguro.POSPUESTO,
                    estado_resultante=EstadoOperativoSeguro.POSPUESTO,
                    nota_corta="y",
                    siguiente_paso="y",
                    timestamp=datetime(2026, 3, 13, tzinfo=UTC),
                ),
            )
        }
    )
    servicio = CierreSemanalSeguroService(
        _AgendaFake(plan), _ColaFake(cola), _AnaliticaFake(_resumen()), _CampaniasFake((campania,)), repo
    )

    resumen = servicio.construir_resumen_semana(date(2026, 3, 14))

    assert resumen.cumplimiento.porcentaje_cumplimiento == 33.33
    assert any(item.codigo == "POSPOSICION_REPETIDA" for item in resumen.desvios)
    assert any("renovaciones críticas" in item.descripcion.lower() for item in resumen.bloqueos)
    assert resumen.aprendizaje.recomendacion_semana_siguiente
