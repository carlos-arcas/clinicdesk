from __future__ import annotations

import logging

from clinicdesk.app.application.seguros.economia_valor import PrioridadValorSeguro
from clinicdesk.app.application.seguros.forecast_comercial_calculos import (
    accion_general,
    cautela_general,
    cautela_por_muestra,
    factor_horizonte,
    ratio_con_guardrail,
    ratio_convertidas,
    ratio_renovacion_salvable,
    riesgo_general,
    valor_total_esperado,
)
from clinicdesk.app.application.seguros.forecast_contratos import (
    CampaniaForecast,
    CohorteForecast,
    DesvioObjetivoSeguro,
    EscenarioComercialSeguro,
    EstadoObjetivoSeguro,
    ForecastComercialSeguro,
    HorizonteForecastSeguro,
    NivelCautelaForecastSeguro,
    ObjetivoComercialSeguro,
    ProyeccionCampaniaSeguro,
    ProyeccionCohorteSeguro,
    RecomendacionEstrategicaSeguro,
)
from clinicdesk.app.domain.seguros import OportunidadSeguro, RenovacionSeguro

LOGGER = logging.getLogger(__name__)


class ForecastComercialSeguroService:
    _UMBRAL_MUESTRA = 4

    def construir_forecast(
        self,
        oportunidades: tuple[OportunidadSeguro, ...],
        renovaciones: tuple[RenovacionSeguro, ...],
        campanias: tuple[CampaniaForecast, ...],
        cohortes: tuple[CohorteForecast, ...],
        prioridades_valor: tuple[PrioridadValorSeguro, ...],
        horizonte: HorizonteForecastSeguro = HorizonteForecastSeguro.DIAS_30,
    ) -> ForecastComercialSeguro:
        conversion_base = ratio_convertidas(oportunidades, self._UMBRAL_MUESTRA)
        renovacion_base = ratio_renovacion_salvable(renovaciones, self._UMBRAL_MUESTRA)
        factor = factor_horizonte(horizonte.value)
        volumen = len(oportunidades)
        cautela = NivelCautelaForecastSeguro(cautela_general(volumen, conversion_base, renovacion_base))
        forecast = ForecastComercialSeguro(
            horizonte=horizonte,
            base_calculo=f"cartera={volumen}|renovaciones={len(renovaciones)}|horizonte={horizonte.value}",
            conversiones_esperadas=round(volumen * (conversion_base or 0.22) * factor),
            renovaciones_salvables_esperadas=round(len(renovaciones) * (renovacion_base or 0.35) * factor),
            volumen_esperado=volumen,
            valor_esperado=valor_total_esperado(prioridades_valor, factor),
            cautela=cautela,
            riesgo_principal=riesgo_general(cautela.value, conversion_base, renovacion_base),
            accion_sugerida=accion_general(cautela.value),
            proyecciones_campania=self._proyectar_campanias(campanias, conversion_base),
            proyecciones_cohorte=self._proyectar_cohortes(cohortes, prioridades_valor),
        )
        LOGGER.info(
            "forecast_seguro_generado",
            extra={"volumen": volumen, "conversiones_esperadas": forecast.conversiones_esperadas},
        )
        return forecast

    def construir_escenarios(
        self, forecast: ForecastComercialSeguro, renovaciones_en_riesgo: int
    ) -> tuple[EscenarioComercialSeguro, ...]:
        return (
            self._escenario("priorizar_renovaciones", forecast, 0.82, 1.1, renovaciones_en_riesgo, "Reduce fuga."),
            self._escenario("priorizar_migraciones", forecast, 1.12, 0.92, forecast.volumen_esperado, "Más altas."),
            self._escenario(
                "priorizar_valor_alto", forecast, 0.9, 1.18, max(2, forecast.volumen_esperado // 2), "Más valor."
            ),
            self._escenario("priorizar_volumen", forecast, 1.2, 0.85, forecast.volumen_esperado, "Más cobertura."),
        )

    def evaluar_objetivos(
        self, forecast: ForecastComercialSeguro, objetivos: tuple[ObjetivoComercialSeguro, ...]
    ) -> tuple[DesvioObjetivoSeguro, ...]:
        proyecciones = {
            "conversiones": float(forecast.conversiones_esperadas),
            "renovaciones": float(forecast.renovaciones_salvables_esperadas),
            "valor_esperado": forecast.valor_esperado,
        }
        return tuple(self._evaluar_objetivo(item, proyecciones, forecast.cautela) for item in objetivos)

    def recomendar_estrategia(
        self, escenarios: tuple[EscenarioComercialSeguro, ...], desvios: tuple[DesvioObjetivoSeguro, ...]
    ) -> RecomendacionEstrategicaSeguro:
        mejor = max(escenarios, key=lambda item: item.valor_esperado)
        bloqueos = sum(1 for item in desvios if item.estado is EstadoObjetivoSeguro.POR_DEBAJO)
        return RecomendacionEstrategicaSeguro(
            foco=mejor.estrategia,
            base_calculo=f"escenario={mejor.estrategia}|desvios_criticos={bloqueos}",
            valor_esperado=mejor.valor_esperado,
            volumen_esperado=mejor.tamano_poblacion,
            cautela=mejor.cautela,
            riesgo_principal=mejor.riesgo_principal,
            accion_sugerida="EJECUTAR_CON_CONTROL_SEMANAL" if bloqueos <= 1 else "PRIORIZAR_CIERRE_DE_BRECHAS",
            por_que=mejor.explicacion,
        )

    def objetivos_default(self, horizonte: HorizonteForecastSeguro) -> tuple[ObjetivoComercialSeguro, ...]:
        return (
            ObjetivoComercialSeguro("conversiones", 8, "casos", horizonte),
            ObjetivoComercialSeguro("renovaciones", 5, "casos", horizonte),
            ObjetivoComercialSeguro("valor_esperado", 2800.0, "eur", horizonte),
        )

    def _proyectar_campanias(
        self, campanias: tuple[CampaniaForecast, ...], conversion_base: float | None
    ) -> tuple[ProyeccionCampaniaSeguro, ...]:
        salida: list[ProyeccionCampaniaSeguro] = []
        for item in campanias:
            conversion = ratio_con_guardrail(conversion_base, item.tamano_estimado, self._UMBRAL_MUESTRA)
            salida.append(
                ProyeccionCampaniaSeguro(
                    id_campania=item.id_campania,
                    base_calculo=f"tamano={item.tamano_estimado}|motivo={item.motivo}",
                    volumen_esperado=item.tamano_estimado,
                    conversion_esperada=conversion,
                    valor_esperado=round(item.tamano_estimado * 180 * (conversion or 0.2), 2),
                    cautela=NivelCautelaForecastSeguro(cautela_por_muestra(item.tamano_estimado)),
                    riesgo_principal="MUESTRA_CORTA"
                    if item.tamano_estimado < self._UMBRAL_MUESTRA
                    else "RIESGO_CONTROLADO",
                    accion_sugerida=item.accion_recomendada,
                )
            )
        return tuple(sorted(salida, key=lambda item: item.valor_esperado, reverse=True)[:3])

    def _proyectar_cohortes(
        self, cohortes: tuple[CohorteForecast, ...], prioridades_valor: tuple[PrioridadValorSeguro, ...]
    ) -> tuple[ProyeccionCohorteSeguro, ...]:
        valor_promedio = (
            round(sum(item.score_impacto for item in prioridades_valor[:8]) * 220, 2) if prioridades_valor else 0.0
        )
        salida: list[ProyeccionCohorteSeguro] = []
        for cohorte in cohortes[:5]:
            conversion = ratio_con_guardrail(cohorte.tasa_conversion, cohorte.tamano, self._UMBRAL_MUESTRA)
            salida.append(
                ProyeccionCohorteSeguro(
                    nombre=f"{cohorte.dimension}:{cohorte.nombre}",
                    base_calculo=f"tamano={cohorte.tamano}|friccion={cohorte.friccion_principal}",
                    volumen_esperado=cohorte.tamano,
                    conversion_esperada=conversion,
                    valor_esperado=round((conversion or 0.15) * cohorte.tamano * max(80.0, valor_promedio), 2),
                    cautela=NivelCautelaForecastSeguro(cautela_por_muestra(cohorte.tamano)),
                    riesgo_principal="CONVERSION_INCERTA" if conversion is None else "RIESGO_CONTROLADO",
                    accion_sugerida=cohorte.accion_sugerida,
                )
            )
        return tuple(sorted(salida, key=lambda item: item.valor_esperado, reverse=True)[:3])

    def _escenario(
        self,
        estrategia: str,
        forecast: ForecastComercialSeguro,
        factor_conversion: float,
        factor_valor: float,
        tamano: int,
        explicacion: str,
    ) -> EscenarioComercialSeguro:
        conversion = round(
            min(1.0, (forecast.conversiones_esperadas / max(1, forecast.volumen_esperado)) * factor_conversion), 4
        )
        return EscenarioComercialSeguro(
            estrategia=estrategia,
            base_calculo=f"factor_conv={factor_conversion}|factor_valor={factor_valor}",
            tamano_poblacion=tamano,
            conversion_esperada=conversion,
            valor_esperado=round(forecast.valor_esperado * factor_valor, 2),
            cautela=forecast.cautela,
            riesgo_principal=forecast.riesgo_principal,
            explicacion=explicacion,
        )

    def _evaluar_objetivo(
        self,
        objetivo: ObjetivoComercialSeguro,
        proyecciones: dict[str, float],
        cautela: NivelCautelaForecastSeguro,
    ) -> DesvioObjetivoSeguro:
        proyectado = proyecciones.get(objetivo.nombre)
        if proyectado is None or cautela is NivelCautelaForecastSeguro.ALTA:
            estado = EstadoObjetivoSeguro.EVIDENCIA_INSUFICIENTE
        elif proyectado < objetivo.valor_objetivo * 0.92:
            estado = EstadoObjetivoSeguro.POR_DEBAJO
        elif proyectado > objetivo.valor_objetivo * 1.08:
            estado = EstadoObjetivoSeguro.POR_ENCIMA
        else:
            estado = EstadoObjetivoSeguro.EN_LINEA
        return DesvioObjetivoSeguro(
            objetivo=objetivo,
            valor_proyectado=round(proyectado or 0.0, 2),
            brecha=round((proyectado or 0.0) - objetivo.valor_objetivo, 2),
            estado=estado,
            base_calculo=f"objetivo={objetivo.nombre}|cautela={cautela.value}",
            explicacion=f"Estado {estado.value} por comparación contra objetivo {objetivo.valor_objetivo}.",
        )
