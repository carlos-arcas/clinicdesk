from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class CampaniaForecast(Protocol):
    id_campania: str
    tamano_estimado: int
    motivo: str
    accion_recomendada: str


class CohorteForecast(Protocol):
    dimension: str
    nombre: str
    tamano: int
    tasa_conversion: float | None
    friccion_principal: str
    accion_sugerida: str


class HorizonteForecastSeguro(str, Enum):
    DIAS_30 = "30D"
    DIAS_60 = "60D"
    DIAS_90 = "90D"


class NivelCautelaForecastSeguro(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class EstadoObjetivoSeguro(str, Enum):
    EN_LINEA = "EN_LINEA"
    POR_DEBAJO = "POR_DEBAJO"
    POR_ENCIMA = "POR_ENCIMA"
    EVIDENCIA_INSUFICIENTE = "EVIDENCIA_INSUFICIENTE"


@dataclass(frozen=True, slots=True)
class ProyeccionCampaniaSeguro:
    id_campania: str
    base_calculo: str
    volumen_esperado: int
    conversion_esperada: float | None
    valor_esperado: float
    cautela: NivelCautelaForecastSeguro
    riesgo_principal: str
    accion_sugerida: str


@dataclass(frozen=True, slots=True)
class ProyeccionCohorteSeguro:
    nombre: str
    base_calculo: str
    volumen_esperado: int
    conversion_esperada: float | None
    valor_esperado: float
    cautela: NivelCautelaForecastSeguro
    riesgo_principal: str
    accion_sugerida: str


@dataclass(frozen=True, slots=True)
class ForecastComercialSeguro:
    horizonte: HorizonteForecastSeguro
    base_calculo: str
    conversiones_esperadas: int
    renovaciones_salvables_esperadas: int
    volumen_esperado: int
    valor_esperado: float
    cautela: NivelCautelaForecastSeguro
    riesgo_principal: str
    accion_sugerida: str
    proyecciones_campania: tuple[ProyeccionCampaniaSeguro, ...]
    proyecciones_cohorte: tuple[ProyeccionCohorteSeguro, ...]


@dataclass(frozen=True, slots=True)
class EscenarioComercialSeguro:
    estrategia: str
    base_calculo: str
    tamano_poblacion: int
    conversion_esperada: float | None
    valor_esperado: float
    cautela: NivelCautelaForecastSeguro
    riesgo_principal: str
    explicacion: str


@dataclass(frozen=True, slots=True)
class ObjetivoComercialSeguro:
    nombre: str
    valor_objetivo: float
    unidad: str
    horizonte: HorizonteForecastSeguro


@dataclass(frozen=True, slots=True)
class DesvioObjetivoSeguro:
    objetivo: ObjetivoComercialSeguro
    valor_proyectado: float
    brecha: float
    estado: EstadoObjetivoSeguro
    base_calculo: str
    explicacion: str


@dataclass(frozen=True, slots=True)
class RecomendacionEstrategicaSeguro:
    foco: str
    base_calculo: str
    valor_esperado: float
    volumen_esperado: int
    cautela: NivelCautelaForecastSeguro
    riesgo_principal: str
    accion_sugerida: str
    por_que: str
