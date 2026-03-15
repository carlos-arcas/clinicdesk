from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.seguros import (
    EstadoObjetivoSeguro,
    ForecastComercialSeguroService,
    NivelCautelaForecastSeguro,
)
from clinicdesk.app.application.seguros.analitica_ejecutiva import CampaniaAccionableSeguro, CohorteSeguro
from clinicdesk.app.application.seguros.economia_valor import (
    CategoriaValorEsperadoSeguro,
    NivelCautelaEconomicaSeguro,
    PrioridadValorSeguro,
)
from clinicdesk.app.domain.seguros import (
    EstadoOportunidadSeguro,
    OportunidadSeguro,
    RenovacionSeguro,
    ResultadoRenovacionSeguro,
)
from clinicdesk.app.domain.seguros.comercial import CandidatoSeguro


@dataclass(frozen=True)
class _Resultado:
    value: str


def _oportunidad(idx: int, convertida: bool) -> OportunidadSeguro:
    return OportunidadSeguro(
        id_oportunidad=f"opp-{idx}",
        candidato=CandidatoSeguro(f"cand-{idx}", f"pac-{idx}", "SEG"),
        plan_origen_id="externo_basico",
        plan_destino_id="clinica_esencial",
        estado_actual=EstadoOportunidadSeguro.CONVERTIDA if convertida else EstadoOportunidadSeguro.EN_SEGUIMIENTO,
        clasificacion_motor="MEDIA",
        perfil_comercial=None,
        evaluacion_fit=None,
        seguimientos=(),
        resultado_comercial=_Resultado("CONVERTIDO") if convertida else None,
    )


def _renovacion(idx: int, pendiente: bool) -> RenovacionSeguro:
    from datetime import date, timedelta

    return RenovacionSeguro(
        id_renovacion=f"ren-{idx}",
        id_oportunidad=f"opp-{idx}",
        plan_vigente_id="clinica_esencial",
        fecha_renovacion=date(2026, 3, 31) + timedelta(days=idx),
        revision_pendiente=pendiente,
        resultado=ResultadoRenovacionSeguro.PENDIENTE,
    )


def _campania() -> CampaniaAccionableSeguro:
    return CampaniaAccionableSeguro(
        id_campania="camp-1",
        titulo="test",
        criterio="fit",
        tamano_estimado=6,
        motivo="base",
        accion_recomendada="accion",
        cautela="media",
        ids_oportunidad=("opp-1",),
    )


def _cohorte() -> CohorteSeguro:
    return CohorteSeguro("segmento", "PYME", 7, 0.4, "precio", "cierre", "insistir")


def _prioridad() -> PrioridadValorSeguro:
    return PrioridadValorSeguro(
        id_oportunidad="opp-1",
        base_calculo="base",
        score_impacto=0.7,
        categoria_valor=CategoriaValorEsperadoSeguro.RAZONABLE,
        riesgo_economico=NivelCautelaEconomicaSeguro.MEDIA,
        accion_sugerida="accion",
        explicacion_humana="ok",
    )


def test_forecast_prudente_con_base_suficiente() -> None:
    servicio = ForecastComercialSeguroService()
    oportunidades = tuple(_oportunidad(idx, convertida=idx % 2 == 0) for idx in range(1, 7))
    renovaciones = tuple(_renovacion(idx, pendiente=idx % 2 == 0) for idx in range(1, 7))

    forecast = servicio.construir_forecast(oportunidades, renovaciones, (_campania(),), (_cohorte(),), (_prioridad(),))
    escenarios = servicio.construir_escenarios(forecast, renovaciones_en_riesgo=2)
    desvios = servicio.evaluar_objetivos(forecast, servicio.objetivos_default(forecast.horizonte))
    recomendacion = servicio.recomendar_estrategia(escenarios, desvios)

    assert forecast.cautela in {NivelCautelaForecastSeguro.BAJA, NivelCautelaForecastSeguro.MEDIA}
    assert forecast.proyecciones_campania
    assert escenarios[0].tamano_poblacion == 2
    assert any(item.estado in {EstadoObjetivoSeguro.EN_LINEA, EstadoObjetivoSeguro.POR_DEBAJO} for item in desvios)
    assert recomendacion.foco


def test_guardrail_forecast_con_muestra_insuficiente() -> None:
    servicio = ForecastComercialSeguroService()
    forecast = servicio.construir_forecast((_oportunidad(1, convertida=False),), (), (_campania(),), (_cohorte(),), ())
    desvios = servicio.evaluar_objetivos(forecast, servicio.objetivos_default(forecast.horizonte))

    assert forecast.cautela is NivelCautelaForecastSeguro.ALTA
    assert all(item.estado is EstadoObjetivoSeguro.EVIDENCIA_INSUFICIENTE for item in desvios)
