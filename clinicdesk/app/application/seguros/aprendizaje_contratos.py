from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricaAprendizajeComercialSeguro:
    poblacion_analizada: str
    tamano_muestra: int
    metrica_principal: float | None
    senal_efectividad: str
    cautela_muestral: str
    accion_recomendada: str


@dataclass(frozen=True, slots=True)
class EfectividadCampaniaSeguro:
    id_campania: str
    nombre_campania: str
    poblacion_analizada: str
    tamano_muestra: int
    metrica_principal: float | None
    senal_efectividad: str
    cautela_muestral: str
    accion_recomendada: str


@dataclass(frozen=True, slots=True)
class InsightArgumentoSeguro:
    segmento: str
    argumento: str
    poblacion_analizada: str
    tamano_muestra: int
    metrica_principal: float | None
    senal_efectividad: str
    cautela_muestral: str
    accion_recomendada: str


@dataclass(frozen=True, slots=True)
class InsightPlanSeguro:
    segmento: str
    plan_propuesto_id: str
    poblacion_analizada: str
    tamano_muestra: int
    metrica_principal: float | None
    senal_efectividad: str
    cautela_muestral: str
    accion_recomendada: str


@dataclass(frozen=True, slots=True)
class InsightSegmentoSeguro:
    eje: str
    valor: str
    poblacion_analizada: str
    tamano_muestra: int
    metrica_principal: float | None
    senal_efectividad: str
    cautela_muestral: str
    accion_recomendada: str


@dataclass(frozen=True, slots=True)
class PlaybookComercialSeguro:
    segmento_objetivo: str
    plan_sugerido: str
    argumento_principal: str
    objecion_a_vigilar: str
    siguiente_accion_sugerida: str
    cautela_muestral: str


@dataclass(frozen=True, slots=True)
class RecomendacionCampaniaSeguro:
    segmento: str
    campania_recomendada: str
    metrica_base: MetricaAprendizajeComercialSeguro


@dataclass(frozen=True, slots=True)
class PanelAprendizajeComercialSeguro:
    efectividad_campanias: tuple[EfectividadCampaniaSeguro, ...]
    insights_segmentos: tuple[InsightSegmentoSeguro, ...]
    insights_argumentos: tuple[InsightArgumentoSeguro, ...]
    insights_planes: tuple[InsightPlanSeguro, ...]
    playbooks: tuple[PlaybookComercialSeguro, ...]
    recomendaciones_campania: tuple[RecomendacionCampaniaSeguro, ...]
