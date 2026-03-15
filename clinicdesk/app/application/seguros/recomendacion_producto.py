from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from clinicdesk.app.application.seguros.catalogo_planes import CatalogoPlanesSeguro
from clinicdesk.app.application.seguros.scoring_comercial import ScoringComercialSeguroService
from clinicdesk.app.domain.seguros.comercial import EstadoOportunidadSeguro, OportunidadSeguro, ResultadoComercialSeguro
from clinicdesk.app.domain.seguros.segmentacion import (
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    SensibilidadPrecioSeguro,
)


class MotivoRecomendacionPlan(str, Enum):
    AHORRO = "AHORRO"
    COBERTURA_UTIL = "COBERTURA_UTIL"
    CONTINUIDAD_CLINICA = "CONTINUIDAD_CLINICA"
    MIGRACION_FAVORABLE = "MIGRACION_FAVORABLE"
    AJUSTE_PERFIL = "AJUSTE_PERFIL"
    BASE_INSUFICIENTE = "BASE_INSUFICIENTE"


class SemaforoRenovacionSeguro(str, Enum):
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"
    EVIDENCIA_INSUFICIENTE = "EVIDENCIA_INSUFICIENTE"


@dataclass(frozen=True, slots=True)
class RecomendacionPlanSeguro:
    id_oportunidad: str
    plan_recomendado_id: str | None
    plan_alternativo_id: str | None
    motivo_principal: MotivoRecomendacionPlan
    objecion_a_vigilar: str
    confianza: float
    cautela: str


@dataclass(frozen=True, slots=True)
class RiesgoRenovacionSeguro:
    id_oportunidad: str
    semaforo: SemaforoRenovacionSeguro
    score_riesgo: float
    riesgo_principal: str
    evidencia: str
    cautela: str


@dataclass(frozen=True, slots=True)
class ArgumentoComercialSeguro:
    angulo_principal: str
    evidencia_principal: str
    contraargumento_cautela: str


@dataclass(frozen=True, slots=True)
class AccionRetencionSeguro:
    accion_sugerida: str
    motivo: str
    limite_informacion: str


@dataclass(frozen=True, slots=True)
class DiagnosticoComercialSeguro:
    recomendacion_plan: RecomendacionPlanSeguro
    riesgo_renovacion: RiesgoRenovacionSeguro
    argumento_comercial: ArgumentoComercialSeguro
    accion_retencion: AccionRetencionSeguro


class RecomendadorProductoSeguroService:
    def __init__(self, catalogo: CatalogoPlanesSeguro, scoring: ScoringComercialSeguroService) -> None:
        self._catalogo = catalogo
        self._scoring = scoring

    def evaluar_oportunidad(self, oportunidad: OportunidadSeguro) -> DiagnosticoComercialSeguro:
        recomendacion = self._recomendar_plan(oportunidad)
        riesgo = self._estimar_riesgo_renovacion(oportunidad)
        argumento = self._construir_argumento(oportunidad, recomendacion)
        accion = self._sugerir_accion(recomendacion, riesgo)
        return DiagnosticoComercialSeguro(recomendacion, riesgo, argumento, accion)

    def _recomendar_plan(self, oportunidad: OportunidadSeguro) -> RecomendacionPlanSeguro:
        perfil = oportunidad.perfil_comercial
        evaluacion = oportunidad.evaluacion_fit
        if perfil is None or evaluacion is None:
            return RecomendacionPlanSeguro(
                id_oportunidad=oportunidad.id_oportunidad,
                plan_recomendado_id=None,
                plan_alternativo_id=None,
                motivo_principal=MotivoRecomendacionPlan.BASE_INSUFICIENTE,
                objecion_a_vigilar="SIN_PERFIL_COMERCIAL",
                confianza=0.2,
                cautela="Base insuficiente para recomendar plan fuerte; completar perfil y fit.",
            )
        candidatos = self._catalogo.listar_planes_clinica()
        puntuados = sorted(
            ((self._score_plan(oportunidad, plan.id_plan), plan.id_plan) for plan in candidatos),
            reverse=True,
        )
        mejor_score, mejor_plan = puntuados[0]
        alternativo = puntuados[1][1] if len(puntuados) > 1 else None
        base_muestras = len(self._scoring.construir_dataset())
        sin_base_robusta = mejor_score < 0.3
        rechazo_activo = oportunidad.resultado_comercial is ResultadoComercialSeguro.RECHAZADO
        fit_fragil = (
            evaluacion.encaje_plan.value == "BAJO" and perfil.sensibilidad_precio is SensibilidadPrecioSeguro.ALTA
        )
        if sin_base_robusta and (rechazo_activo or fit_fragil):
            return RecomendacionPlanSeguro(
                id_oportunidad=oportunidad.id_oportunidad,
                plan_recomendado_id=None,
                plan_alternativo_id=mejor_plan,
                motivo_principal=MotivoRecomendacionPlan.BASE_INSUFICIENTE,
                objecion_a_vigilar=perfil.objecion_principal.value,
                confianza=0.35,
                cautela="No hay ventaja comercial robusta: sostener conversación consultiva y recabar más señales.",
            )
        motivo = _motivo_recomendacion(oportunidad)
        confianza = min(0.9, 0.45 + (mejor_score / 12) + min(base_muestras, 10) * 0.01)
        return RecomendacionPlanSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            plan_recomendado_id=mejor_plan,
            plan_alternativo_id=alternativo,
            motivo_principal=motivo,
            objecion_a_vigilar=perfil.objecion_principal.value,
            confianza=round(confianza, 3),
            cautela="Recomendación orientativa: confirmar expectativas de cobertura y capacidad de pago antes de cerrar.",
        )

    def _estimar_riesgo_renovacion(self, oportunidad: OportunidadSeguro) -> RiesgoRenovacionSeguro:
        perfil = oportunidad.perfil_comercial
        evaluacion = oportunidad.evaluacion_fit
        if perfil is None and evaluacion is None and not oportunidad.seguimientos:
            return RiesgoRenovacionSeguro(
                id_oportunidad=oportunidad.id_oportunidad,
                semaforo=SemaforoRenovacionSeguro.EVIDENCIA_INSUFICIENTE,
                score_riesgo=0.5,
                riesgo_principal="SIN_HISTORICO_OPERATIVO",
                evidencia="Sin señales suficientes para estimar fuga con prudencia.",
                cautela="Completar seguimiento comercial y feedback de renovación.",
            )
        score = 0.35
        if oportunidad.estado_actual is EstadoOportunidadSeguro.PENDIENTE_RENOVACION:
            score += 0.1
        if oportunidad.clasificacion_motor == "DESFAVORABLE":
            score += 0.2
        if oportunidad.clasificacion_motor == "REVISAR":
            score += 0.08
        if oportunidad.clasificacion_motor == "FAVORABLE":
            score -= 0.08
        if evaluacion and evaluacion.encaje_plan.value == "BAJO":
            score += 0.25
        if evaluacion and evaluacion.encaje_plan.value == "ALTO":
            score -= 0.1
        if perfil and perfil.sensibilidad_precio is SensibilidadPrecioSeguro.ALTA:
            score += 0.18
        if perfil and perfil.sensibilidad_precio is SensibilidadPrecioSeguro.MEDIA:
            score += 0.08
        if perfil and perfil.objecion_principal is ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO:
            score += 0.15
        if len(oportunidad.seguimientos) >= 3:
            score += 0.1
        if oportunidad.resultado_comercial is ResultadoComercialSeguro.RECHAZADO:
            score += 0.2
        if oportunidad.resultado_comercial is ResultadoComercialSeguro.POSPUESTO:
            score += 0.12
        if oportunidad.resultado_comercial is ResultadoComercialSeguro.CONVERTIDO:
            score -= 0.08
        score = round(min(max(score, 0.03), 0.97), 3)
        semaforo = _semaforo_riesgo(score)
        return RiesgoRenovacionSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            semaforo=semaforo,
            score_riesgo=score,
            riesgo_principal=_riesgo_principal(oportunidad),
            evidencia=_evidencia_riesgo(oportunidad),
            cautela="Riesgo orientativo para priorización comercial; requiere validación humana en cartera.",
        )

    def _construir_argumento(
        self, oportunidad: OportunidadSeguro, recomendacion: RecomendacionPlanSeguro
    ) -> ArgumentoComercialSeguro:
        perfil = oportunidad.perfil_comercial
        if perfil and perfil.sensibilidad_precio is SensibilidadPrecioSeguro.ALTA:
            return ArgumentoComercialSeguro(
                angulo_principal="AHORRO_TOTAL",
                evidencia_principal="Priorizar coste mensual y copagos previsibles para reducir objeción de precio.",
                contraargumento_cautela="Validar que el ahorro no sacrifica coberturas críticas del paciente.",
            )
        if perfil and perfil.necesidad_principal is NecesidadPrincipalSeguro.CONTINUIDAD_MEDICA:
            return ArgumentoComercialSeguro(
                angulo_principal="CONTINUIDAD_CLINICA",
                evidencia_principal="Refuerza continuidad asistencial y coordinación con la clínica.",
                contraargumento_cautela="Confirmar agenda y especialidades realmente relevantes para el caso.",
            )
        if recomendacion.motivo_principal is MotivoRecomendacionPlan.MIGRACION_FAVORABLE:
            return ArgumentoComercialSeguro(
                angulo_principal="MIGRACION_FAVORABLE",
                evidencia_principal="La comparativa muestra mejoras netas y menor fricción de cambio.",
                contraargumento_cautela="Explicar pérdidas o advertencias para evitar promesas excesivas.",
            )
        return ArgumentoComercialSeguro(
            angulo_principal="COBERTURA_UTIL",
            evidencia_principal="Enfatizar coberturas alineadas al perfil y uso esperado.",
            contraargumento_cautela="No sobreprometer cobertura sin revisión de exclusiones y carencias.",
        )

    def _sugerir_accion(
        self, recomendacion: RecomendacionPlanSeguro, riesgo: RiesgoRenovacionSeguro
    ) -> AccionRetencionSeguro:
        if riesgo.semaforo is SemaforoRenovacionSeguro.ALTO:
            return AccionRetencionSeguro(
                accion_sugerida="REVISAR_RENOVACION_PRIORITARIA",
                motivo="Riesgo alto de fuga con señales de fricción comercial acumulada.",
                limite_informacion="No automatizar decisión: confirmar situación contractual y motivos actuales.",
            )
        if riesgo.semaforo is SemaforoRenovacionSeguro.EVIDENCIA_INSUFICIENTE:
            return AccionRetencionSeguro(
                accion_sugerida="SEGUIMIENTO_MANUAL_RECOMENDADO",
                motivo="No hay suficiente histórico para una recomendación fuerte.",
                limite_informacion="Completar interacción comercial antes de insistir o descartar.",
            )
        if recomendacion.plan_recomendado_id is None:
            return AccionRetencionSeguro(
                accion_sugerida="NO_INSISTIR_AUN",
                motivo="La recomendación de plan no es robusta y puede erosionar confianza.",
                limite_informacion="Recabar objeciones reales y datos de uso antes de nueva propuesta.",
            )
        if recomendacion.objecion_a_vigilar == ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO.value:
            return AccionRetencionSeguro(
                accion_sugerida="REVISAR_OBJECION_PRECIO",
                motivo="La objeción de precio domina el discurso y puede bloquear cierre/renovación.",
                limite_informacion="No usar descuentos automáticos sin validar margen y cobertura.",
            )
        return AccionRetencionSeguro(
            accion_sugerida="OFERTAR_PLAN_RECOMENDADO",
            motivo="Existe base suficiente para proponer plan y avanzar siguiente paso.",
            limite_informacion="Confirmar elegibilidad final y expectativas del cliente.",
        )

    def _score_plan(self, oportunidad: OportunidadSeguro, plan_id: str) -> float:
        plan = self._catalogo.obtener_por_id(plan_id)
        plan_origen = self._catalogo.obtener_por_id(oportunidad.plan_origen_id)
        perfil = oportunidad.perfil_comercial
        evaluacion = oportunidad.evaluacion_fit
        score = 0.0
        if oportunidad.clasificacion_motor == "FAVORABLE":
            score += 2.0
        if oportunidad.clasificacion_motor == "REVISAR":
            score -= 1.0
        if evaluacion and evaluacion.encaje_plan.value == "ALTO":
            score += 2.0
        if evaluacion and evaluacion.encaje_plan.value == "MEDIO":
            score += 1.0
        if evaluacion and evaluacion.encaje_plan.value in {"BAJO", "REVISAR"}:
            score -= 2.0
        if perfil and perfil.necesidad_principal is NecesidadPrincipalSeguro.AHORRO_COSTE:
            score += 1.8 if plan.cuota_mensual <= plan_origen.cuota_mensual else -1.0
        if perfil and perfil.necesidad_principal in {
            NecesidadPrincipalSeguro.COBERTURA_FAMILIAR,
            NecesidadPrincipalSeguro.ACCESO_ESPECIALISTAS,
        }:
            score += (
                1.2 if any(item.codigo == "hospitalizacion" and item.incluida for item in plan.coberturas) else -0.4
            )
        if perfil and perfil.sensibilidad_precio is SensibilidadPrecioSeguro.ALTA and plan.cuota_mensual > 70:
            score -= 2.0
        if perfil and perfil.objecion_principal is ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO:
            score += 0.4 if plan.cuota_mensual <= plan_origen.cuota_mensual else -1.2
        if perfil and MotivacionCompraSeguro.CONFIANZA_EN_CLINICA in perfil.motivaciones:
            score += 0.8
        return round(score, 3)


def _motivo_recomendacion(oportunidad: OportunidadSeguro) -> MotivoRecomendacionPlan:
    perfil = oportunidad.perfil_comercial
    evaluacion = oportunidad.evaluacion_fit
    if perfil and perfil.necesidad_principal is NecesidadPrincipalSeguro.AHORRO_COSTE:
        return MotivoRecomendacionPlan.AHORRO
    if perfil and perfil.necesidad_principal is NecesidadPrincipalSeguro.CONTINUIDAD_MEDICA:
        return MotivoRecomendacionPlan.CONTINUIDAD_CLINICA
    if oportunidad.clasificacion_motor == "FAVORABLE":
        return MotivoRecomendacionPlan.MIGRACION_FAVORABLE
    if evaluacion and evaluacion.encaje_plan.value == "ALTO":
        return MotivoRecomendacionPlan.AJUSTE_PERFIL
    return MotivoRecomendacionPlan.COBERTURA_UTIL


def _semaforo_riesgo(score: float) -> SemaforoRenovacionSeguro:
    if score >= 0.67:
        return SemaforoRenovacionSeguro.ALTO
    if score >= 0.45:
        return SemaforoRenovacionSeguro.MEDIO
    return SemaforoRenovacionSeguro.BAJO


def _riesgo_principal(oportunidad: OportunidadSeguro) -> str:
    perfil = oportunidad.perfil_comercial
    if perfil and perfil.objecion_principal is ObjecionComercialSeguro.PRECIO_PERCIBIDO_ALTO:
        return "PRECIO_PERCIBIDO_ALTO"
    if perfil and perfil.sensibilidad_precio is SensibilidadPrecioSeguro.ALTA:
        return "SENSIBILIDAD_PRECIO_ALTA"
    if oportunidad.evaluacion_fit and oportunidad.evaluacion_fit.encaje_plan.value in {"BAJO", "REVISAR"}:
        return "FIT_COMERCIAL_DEBIL"
    return "RIESGO_COMERCIAL_GENERAL"


def _evidencia_riesgo(oportunidad: OportunidadSeguro) -> str:
    return (
        f"estado={oportunidad.estado_actual.value}|"
        f"motor={oportunidad.clasificacion_motor}|"
        f"seguimientos={len(oportunidad.seguimientos)}"
    )
