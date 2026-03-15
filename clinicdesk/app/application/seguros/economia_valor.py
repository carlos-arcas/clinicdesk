from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from clinicdesk.app.application.seguros.catalogo_planes import CatalogoPlanesSeguro
from clinicdesk.app.application.seguros.economia_valor_calculos import (
    ValorTemporal,
    accion_por_valor,
    categoria_valor,
    cautela_por_categoria,
    estimar_esfuerzo,
    mapear_campania,
    mapear_segmento,
    normalizar_valor,
    penalizacion_cautela,
)
from clinicdesk.app.application.seguros.recomendacion_producto import RecomendadorProductoSeguroService
from clinicdesk.app.application.seguros.scoring_comercial import ScoringComercialSeguroService
from clinicdesk.app.domain.seguros import OportunidadSeguro, RenovacionSeguro


class CategoriaValorEsperadoSeguro(str, Enum):
    ALTO = "ALTO"
    RAZONABLE = "RAZONABLE"
    BAJO = "BAJO"
    EVIDENCIA_INSUFICIENTE = "EVIDENCIA_INSUFICIENTE"


class NivelCautelaEconomicaSeguro(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


@dataclass(frozen=True, slots=True)
class MargenEsperadoPlanSeguro:
    id_oportunidad: str
    plan_id: str
    base_calculo: str
    ingreso_bruto_estimado: float
    esfuerzo_comercial_estimado: float
    margen_estimado: float
    confianza: float
    explicacion_humana: str


@dataclass(frozen=True, slots=True)
class RiesgoEconomicoSeguro:
    id_oportunidad: str
    nivel_cautela: NivelCautelaEconomicaSeguro
    riesgo_principal: str
    accion_sugerida: str
    explicacion_humana: str


@dataclass(frozen=True, slots=True)
class ValorEsperadoOportunidadSeguro:
    id_oportunidad: str
    base_calculo: str
    valor_estimado: float
    categoria: CategoriaValorEsperadoSeguro
    confianza: float
    riesgo_principal: str
    accion_sugerida: str
    explicacion_humana: str


@dataclass(frozen=True, slots=True)
class PrioridadValorSeguro:
    id_oportunidad: str
    base_calculo: str
    score_impacto: float
    categoria_valor: CategoriaValorEsperadoSeguro
    riesgo_economico: NivelCautelaEconomicaSeguro
    accion_sugerida: str
    explicacion_humana: str


@dataclass(frozen=True, slots=True)
class InsightRentabilidadSeguro:
    titulo: str
    base_calculo: str
    valor_estimado: float
    nivel_cautela: NivelCautelaEconomicaSeguro
    riesgo_principal: str
    accion_sugerida: str
    explicacion_humana: str


@dataclass(frozen=True, slots=True)
class CampaniaRentableSeguro:
    nombre: str
    base_calculo: str
    valor_total_estimado: float
    media_valor_estimado: float
    categoria: CategoriaValorEsperadoSeguro
    nivel_cautela: NivelCautelaEconomicaSeguro
    accion_sugerida: str
    explicacion_humana: str


@dataclass(frozen=True, slots=True)
class SegmentoRentableSeguro:
    segmento: str
    base_calculo: str
    valor_total_estimado: float
    conversion_aproximada: float | None
    categoria: CategoriaValorEsperadoSeguro
    nivel_cautela: NivelCautelaEconomicaSeguro
    accion_sugerida: str
    explicacion_humana: str


@dataclass(frozen=True, slots=True)
class PanelValorEconomicoSeguro:
    prioridades: tuple[PrioridadValorSeguro, ...]
    campanias_rentables: tuple[CampaniaRentableSeguro, ...]
    segmentos_rentables: tuple[SegmentoRentableSeguro, ...]
    insights: tuple[InsightRentabilidadSeguro, ...]


class EconomiaValorSeguroService:
    def __init__(
        self,
        catalogo: CatalogoPlanesSeguro,
        scoring: ScoringComercialSeguroService,
        recomendador: RecomendadorProductoSeguroService,
    ) -> None:
        self._catalogo = catalogo
        self._scoring = scoring
        self._recomendador = recomendador

    def construir_panel(
        self,
        oportunidades: tuple[OportunidadSeguro, ...],
        renovaciones: tuple[RenovacionSeguro, ...],
    ) -> PanelValorEconomicoSeguro:
        renovaciones_riesgo = {item.id_oportunidad for item in renovaciones if item.revision_pendiente}
        cartera = self._scoring.priorizar_cartera(oportunidades)
        score_por_oportunidad = {item.id_oportunidad: item.score_prioridad for item in cartera.oportunidades}
        valor_por_oportunidad: dict[str, ValorEsperadoOportunidadSeguro] = {}
        prioridades: list[PrioridadValorSeguro] = []
        for oportunidad in oportunidades:
            valor = self._estimar_valor_esperado(oportunidad, score_por_oportunidad, renovaciones_riesgo)
            valor_por_oportunidad[oportunidad.id_oportunidad] = valor
            prioridades.append(self._priorizar(oportunidad, valor, score_por_oportunidad, renovaciones_riesgo))
        prioridades_ordenadas = tuple(sorted(prioridades, key=lambda item: item.score_impacto, reverse=True))
        campanias = self._resumir_campanias(oportunidades, valor_por_oportunidad)
        segmentos = self._resumir_segmentos(oportunidades, valor_por_oportunidad)
        return PanelValorEconomicoSeguro(
            prioridades=prioridades_ordenadas[:8],
            campanias_rentables=campanias,
            segmentos_rentables=segmentos,
            insights=self._construir_insights(prioridades_ordenadas, campanias, segmentos),
        )

    def _estimar_valor_esperado(
        self,
        oportunidad: OportunidadSeguro,
        score_por_oportunidad: dict[str, float],
        renovaciones_riesgo: set[str],
    ) -> ValorEsperadoOportunidadSeguro:
        margen = self._estimar_margen_plan(oportunidad)
        riesgo = self._estimar_riesgo(oportunidad, margen, renovaciones_riesgo)
        propension = score_por_oportunidad.get(oportunidad.id_oportunidad, 0.5)
        valor = round(
            (margen.margen_estimado * propension) * (1.12 if oportunidad.id_oportunidad in renovaciones_riesgo else 1),
            2,
        )
        confianza = round(min(margen.confianza, 1.0 - penalizacion_cautela(riesgo.nivel_cautela.value)), 3)
        categoria = CategoriaValorEsperadoSeguro(categoria_valor(valor, confianza))
        accion = accion_por_valor(categoria.value, riesgo.nivel_cautela.value)
        return ValorEsperadoOportunidadSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            base_calculo=f"{margen.base_calculo}|propension={round(propension, 3)}",
            valor_estimado=valor,
            categoria=categoria,
            confianza=confianza,
            riesgo_principal=riesgo.riesgo_principal,
            accion_sugerida=accion,
            explicacion_humana=f"valor={valor} con margen prudente y propensión comercial.",
        )

    def _estimar_margen_plan(self, oportunidad: OportunidadSeguro) -> MargenEsperadoPlanSeguro:
        diagnostico = self._recomendador.evaluar_oportunidad(oportunidad)
        plan_id = diagnostico.recomendacion_plan.plan_recomendado_id or oportunidad.plan_destino_id
        plan = self._catalogo.obtener_por_id(plan_id)
        ingreso_bruto = round(plan.cuota_mensual * 12, 2)
        esfuerzo = estimar_esfuerzo(oportunidad)
        prudencia = 0.55 if diagnostico.riesgo_renovacion.semaforo.value == "ALTO" else 0.65
        margen = round(max(0.0, ingreso_bruto * prudencia - esfuerzo), 2)
        return MargenEsperadoPlanSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            plan_id=plan_id,
            base_calculo=f"cuota_anual={ingreso_bruto}|prudencia={prudencia}|esfuerzo={esfuerzo}",
            ingreso_bruto_estimado=ingreso_bruto,
            esfuerzo_comercial_estimado=esfuerzo,
            margen_estimado=margen,
            confianza=diagnostico.recomendacion_plan.confianza,
            explicacion_humana="Margen operativo prudente: ingreso anual estimado menos esfuerzo comercial.",
        )

    def _estimar_riesgo(
        self, oportunidad: OportunidadSeguro, margen: MargenEsperadoPlanSeguro, renovaciones_riesgo: set[str]
    ) -> RiesgoEconomicoSeguro:
        if margen.confianza < 0.45:
            return RiesgoEconomicoSeguro(
                oportunidad.id_oportunidad,
                NivelCautelaEconomicaSeguro.ALTA,
                "BASE_COMERCIAL_INSUFICIENTE",
                "REVISAR_CASO_MANUALMENTE",
                "La confianza comercial es baja.",
            )
        if oportunidad.id_oportunidad in renovaciones_riesgo:
            return RiesgoEconomicoSeguro(
                oportunidad.id_oportunidad,
                NivelCautelaEconomicaSeguro.MEDIA,
                "RENOVACION_CON_FUGA_POTENCIAL",
                "REFORZAR_RENOVACION_DE_ALTO_VALOR",
                "Hay riesgo de fuga.",
            )
        if margen.margen_estimado < 220:
            return RiesgoEconomicoSeguro(
                oportunidad.id_oportunidad,
                NivelCautelaEconomicaSeguro.MEDIA,
                "MARGEN_ESPERADO_ACOTADO",
                "NO_SOBREINVERTIR_ESFUERZO",
                "Margen esperado contenido.",
            )
        return RiesgoEconomicoSeguro(
            oportunidad.id_oportunidad,
            NivelCautelaEconomicaSeguro.BAJA,
            "RIESGO_CONTROLADO",
            "INSISTIR_CON_PRIORIDAD_ALTA",
            "Margen esperado razonable.",
        )

    def _priorizar(
        self,
        oportunidad: OportunidadSeguro,
        valor: ValorEsperadoOportunidadSeguro,
        score_por_oportunidad: dict[str, float],
        renovaciones_riesgo: set[str],
    ) -> PrioridadValorSeguro:
        score_comercial = score_por_oportunidad.get(oportunidad.id_oportunidad, 0.5)
        score_impacto = round(
            min(
                1.0,
                score_comercial * 0.55
                + normalizar_valor(valor.valor_estimado) * 0.45
                + (0.08 if oportunidad.id_oportunidad in renovaciones_riesgo else 0.0),
            ),
            4,
        )
        riesgo = NivelCautelaEconomicaSeguro(cautela_por_categoria(valor.categoria.value, valor.confianza))
        return PrioridadValorSeguro(
            id_oportunidad=oportunidad.id_oportunidad,
            base_calculo=f"score_comercial={round(score_comercial, 3)}|valor={valor.valor_estimado}",
            score_impacto=score_impacto,
            categoria_valor=valor.categoria,
            riesgo_economico=riesgo,
            accion_sugerida=valor.accion_sugerida,
            explicacion_humana=f"Combinación de propensión y valor ({valor.categoria.value}).",
        )

    def _resumir_campanias(
        self,
        oportunidades: tuple[OportunidadSeguro, ...],
        valor_por_oportunidad: dict[str, ValorEsperadoOportunidadSeguro],
    ) -> tuple[CampaniaRentableSeguro, ...]:
        grupos: dict[str, list[ValorTemporal]] = defaultdict(list)
        for oportunidad in oportunidades:
            nombre = oportunidad.perfil_comercial.origen_cliente.value if oportunidad.perfil_comercial else "SIN_ORIGEN"
            valor = valor_por_oportunidad[oportunidad.id_oportunidad]
            grupos[nombre].append(ValorTemporal(valor.id_oportunidad, valor.valor_estimado, valor.confianza))
        resultado = []
        for nombre, valores in grupos.items():
            total, media, categoria, cautela, accion, explicacion = mapear_campania(nombre, tuple(valores))
            resultado.append(
                CampaniaRentableSeguro(
                    nombre,
                    f"oportunidades={len(valores)}|media={media}",
                    total,
                    media,
                    CategoriaValorEsperadoSeguro(categoria),
                    NivelCautelaEconomicaSeguro(cautela),
                    accion,
                    explicacion,
                )
            )
        return tuple(sorted(resultado, key=lambda item: item.valor_total_estimado, reverse=True)[:4])

    def _resumir_segmentos(
        self,
        oportunidades: tuple[OportunidadSeguro, ...],
        valor_por_oportunidad: dict[str, ValorEsperadoOportunidadSeguro],
    ) -> tuple[SegmentoRentableSeguro, ...]:
        grupos: dict[str, list[tuple[OportunidadSeguro, ValorTemporal]]] = defaultdict(list)
        for oportunidad in oportunidades:
            valor = valor_por_oportunidad[oportunidad.id_oportunidad]
            grupos[oportunidad.candidato.segmento].append(
                (oportunidad, ValorTemporal(valor.id_oportunidad, valor.valor_estimado, valor.confianza))
            )
        resultado = []
        for segmento, items in grupos.items():
            total, tasa, categoria, cautela, accion, explicacion = mapear_segmento(segmento, tuple(items))
            resultado.append(
                SegmentoRentableSeguro(
                    segmento,
                    f"oportunidades={len(items)}|conversion={tasa}",
                    total,
                    tasa,
                    CategoriaValorEsperadoSeguro(categoria),
                    NivelCautelaEconomicaSeguro(cautela),
                    accion,
                    explicacion,
                )
            )
        return tuple(sorted(resultado, key=lambda item: item.valor_total_estimado, reverse=True)[:4])

    def _construir_insights(
        self,
        prioridades: tuple[PrioridadValorSeguro, ...],
        campanias: tuple[CampaniaRentableSeguro, ...],
        segmentos: tuple[SegmentoRentableSeguro, ...],
    ) -> tuple[InsightRentabilidadSeguro, ...]:
        if not prioridades:
            return ()
        resultado = [
            InsightRentabilidadSeguro(
                "Oportunidad de mayor impacto esperado",
                prioridades[0].base_calculo,
                round(prioridades[0].score_impacto * 1000, 2),
                prioridades[0].riesgo_economico,
                f"VALOR_{prioridades[0].categoria_valor.value}",
                prioridades[0].accion_sugerida,
                f"Priorizar {prioridades[0].id_oportunidad} por impacto combinado.",
            )
        ]
        if campanias:
            top = campanias[0]
            resultado.append(
                InsightRentabilidadSeguro(
                    "Campaña con mejor retorno prudente",
                    top.base_calculo,
                    top.valor_total_estimado,
                    top.nivel_cautela,
                    f"CAMPANIA_{top.categoria.value}",
                    top.accion_sugerida,
                    top.explicacion_humana,
                )
            )
        if segmentos:
            top_segmento = segmentos[0]
            resultado.append(
                InsightRentabilidadSeguro(
                    "Segmento comercial prioritario",
                    top_segmento.base_calculo,
                    top_segmento.valor_total_estimado,
                    top_segmento.nivel_cautela,
                    f"SEGMENTO_{top_segmento.categoria.value}",
                    top_segmento.accion_sugerida,
                    top_segmento.explicacion_humana,
                )
            )
        return tuple(resultado)
