from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from clinicdesk.app.application.seguros.comercial import RepositorioComercialSeguro
from clinicdesk.app.application.seguros.recomendacion_producto import RecomendadorProductoSeguroService
from clinicdesk.app.application.seguros.scoring_comercial import (
    NivelPrioridadComercialSeguro,
    PrioridadOportunidadSeguro,
    ScoringComercialSeguroService,
)
from clinicdesk.app.domain.seguros.comercial import OportunidadSeguro, RenovacionSeguro
from clinicdesk.app.domain.seguros.cola_operativa import (
    AccionPendienteSeguro,
    ColaTrabajoSeguro,
    EstadoOperativoSeguro,
    GestionOperativaColaSeguro,
    ItemColaComercialSeguro,
    PrioridadTrabajoSeguro,
    RecordatorioSeguimientoSeguro,
    ResultadoGestionColaSeguro,
    TipoItemColaSeguro,
    estado_resultante_por_accion,
)


@dataclass(frozen=True, slots=True)
class SolicitudGestionItemColaSeguro:
    id_oportunidad: str
    accion: AccionPendienteSeguro
    nota_corta: str = ""
    siguiente_paso: str = ""


class ColaTrabajoSeguroService:
    def __init__(
        self,
        repositorio: RepositorioComercialSeguro,
        scoring: ScoringComercialSeguroService,
        recomendador: RecomendadorProductoSeguroService,
    ) -> None:
        self._repositorio = repositorio
        self._scoring = scoring
        self._recomendador = recomendador

    def construir_cola_diaria(self, ahora: datetime | None = None) -> ColaTrabajoSeguro:
        corte = ahora or datetime.now(UTC)
        oportunidades = self._repositorio.listar_oportunidades_por_gestion_operativa()
        renovaciones = {item.id_oportunidad: item for item in self._repositorio.listar_renovaciones_pendientes()}
        prioridades = {
            item.id_oportunidad: item for item in self._scoring.priorizar_cartera(oportunidades).oportunidades
        }
        items = [
            self._construir_item(
                oportunidad,
                prioridades.get(oportunidad.id_oportunidad),
                renovaciones.get(oportunidad.id_oportunidad),
                corte,
            )
            for oportunidad in oportunidades
        ]
        ordenados = tuple(sorted(items, key=lambda item: item.score_prioridad, reverse=True))
        return ColaTrabajoSeguro(fecha_corte=corte, items=ordenados)

    def registrar_gestion(self, solicitud: SolicitudGestionItemColaSeguro) -> ResultadoGestionColaSeguro:
        timestamp = datetime.now(UTC)
        gestion = GestionOperativaColaSeguro(
            id_oportunidad=solicitud.id_oportunidad,
            accion=solicitud.accion,
            estado_resultante=estado_resultante_por_accion(solicitud.accion),
            nota_corta=solicitud.nota_corta,
            siguiente_paso=solicitud.siguiente_paso,
            timestamp=timestamp,
        )
        self._repositorio.guardar_gestion_operativa(gestion)
        return ResultadoGestionColaSeguro(
            id_oportunidad=solicitud.id_oportunidad,
            estado_operativo=gestion.estado_resultante,
            accion_registrada=solicitud.accion,
            timestamp=timestamp,
        )

    def _construir_item(
        self,
        oportunidad: OportunidadSeguro,
        prioridad_scoring: PrioridadOportunidadSeguro | None,
        renovacion: RenovacionSeguro | None,
        corte: datetime,
    ) -> ItemColaComercialSeguro:
        diagnostico = self._recomendador.evaluar_oportunidad(oportunidad)
        ultima_gestion = self._repositorio.obtener_ultima_gestion_operativa(oportunidad.id_oportunidad)
        estado = ultima_gestion.estado_resultante if ultima_gestion else EstadoOperativoSeguro.PENDIENTE
        tipo = _definir_tipo_item(oportunidad, renovacion, corte)
        recordatorio = _construir_recordatorio(renovacion, corte)
        score_base = prioridad_scoring.score_prioridad if prioridad_scoring else 0.25
        score_operativo = _score_operativo(score_base, recordatorio, oportunidad)
        prioridad = _prioridad_operativa(score_operativo)
        if recordatorio and recordatorio.vencido and prioridad is PrioridadTrabajoSeguro.NO_PRIORITARIA:
            prioridad = PrioridadTrabajoSeguro.PRIORITARIA
        motivo = _motivo_prioridad(prioridad_scoring, diagnostico.riesgo_renovacion.semaforo.value, recordatorio)
        accion = _siguiente_accion(prioridad_scoring, diagnostico.accion_retencion.accion_sugerida)
        contexto = f"{oportunidad.plan_origen_id} -> {oportunidad.plan_destino_id}"
        return ItemColaComercialSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            tipo_item=tipo,
            prioridad=prioridad,
            motivo_principal=motivo,
            siguiente_accion_sugerida=accion,
            estado_operativo=estado,
            riesgo_cautela=diagnostico.recomendacion_plan.cautela,
            plan_contexto=contexto,
            score_prioridad=round(score_operativo, 4),
            recordatorio=recordatorio,
            ultima_gestion=ultima_gestion,
        )


def _definir_tipo_item(
    oportunidad: OportunidadSeguro, renovacion: RenovacionSeguro | None, corte: datetime
) -> TipoItemColaSeguro:
    if not renovacion:
        return TipoItemColaSeguro.OPORTUNIDAD
    if renovacion.fecha_renovacion <= corte.date():
        return TipoItemColaSeguro.SEGUIMIENTO_VENCIDO
    return TipoItemColaSeguro.RENOVACION


def _construir_recordatorio(
    renovacion: RenovacionSeguro | None, corte: datetime
) -> RecordatorioSeguimientoSeguro | None:
    if not renovacion:
        return None
    dias = (corte.date() - renovacion.fecha_renovacion).days
    return RecordatorioSeguimientoSeguro(
        fecha_objetivo=renovacion.fecha_renovacion,
        vencido=dias >= 0,
        dias_desfase=max(dias, 0),
    )


def _score_operativo(
    score_base: float, recordatorio: RecordatorioSeguimientoSeguro | None, oportunidad: OportunidadSeguro
) -> float:
    score = score_base
    if recordatorio and recordatorio.vencido:
        score += 0.2 + min(recordatorio.dias_desfase * 0.01, 0.15)
    if oportunidad.perfil_comercial and oportunidad.perfil_comercial.friccion_migracion.value == "ALTA":
        score += 0.05
    if oportunidad.perfil_comercial and oportunidad.perfil_comercial.objecion_principal.value != "SIN_OBJECION":
        score += 0.03
    if oportunidad.seguimientos:
        score += 0.04
    return min(score, 0.98)


def _prioridad_operativa(score: float) -> PrioridadTrabajoSeguro:
    if score >= 0.82:
        return PrioridadTrabajoSeguro.MUY_PRIORITARIA
    if score >= 0.62:
        return PrioridadTrabajoSeguro.PRIORITARIA
    if score >= 0.4:
        return PrioridadTrabajoSeguro.SECUNDARIA
    return PrioridadTrabajoSeguro.NO_PRIORITARIA


def _motivo_prioridad(
    prioridad_scoring: PrioridadOportunidadSeguro | None,
    semaforo_renovacion: str,
    recordatorio: RecordatorioSeguimientoSeguro | None,
) -> str:
    tramos: list[str] = []
    if prioridad_scoring:
        tramos.append(f"Scoring comercial {prioridad_scoring.prioridad.value.lower()}")
    if semaforo_renovacion == "ALTO":
        tramos.append("riesgo de renovacion alto")
    if recordatorio and recordatorio.vencido:
        tramos.append(f"seguimiento vencido +{recordatorio.dias_desfase}d")
    return "; ".join(tramos) if tramos else "Prioridad base por actividad comercial reciente"


def _siguiente_accion(prioridad_scoring: PrioridadOportunidadSeguro | None, accion_retencion: str) -> str:
    if prioridad_scoring and prioridad_scoring.prioridad is NivelPrioridadComercialSeguro.ALTA:
        return "contacto_hoy"
    if "retencion" in accion_retencion.lower() or "renovacion" in accion_retencion.lower():
        return "revisar_renovacion"
    return "seguimiento_planificado"
