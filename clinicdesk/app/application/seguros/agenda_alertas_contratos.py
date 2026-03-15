from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class TipoAlertaComercialSeguro(str, Enum):
    RENOVACION_PROXIMA = "RENOVACION_PROXIMA"
    RENOVACION_VENCIDA = "RENOVACION_VENCIDA"
    SEGUIMIENTO_ATRASADO = "SEGUIMIENTO_ATRASADO"
    OBJETIVO_EN_RIESGO = "OBJETIVO_EN_RIESGO"
    CAMPANIA_SIN_AVANCE = "CAMPANIA_SIN_AVANCE"
    OPORTUNIDAD_CALIENTE_SIN_TOQUE = "OPORTUNIDAD_CALIENTE_SIN_TOQUE"
    CAMPANIA_RECOMENDADA_NO_LANZADA = "CAMPANIA_RECOMENDADA_NO_LANZADA"


class PrioridadAlertaSeguro(str, Enum):
    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"


class EstadoTareaSeguro(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    RESUELTA = "RESUELTA"
    POSPUESTA = "POSPUESTA"
    DESCARTADA = "DESCARTADA"
    VENCIDA = "VENCIDA"


class ReglaAlertaSeguro(str, Enum):
    RENOVACION_MENOR_7_DIAS = "RENOVACION_MENOR_7_DIAS"
    RENOVACION_VENCIDA_SIN_GESTION = "RENOVACION_VENCIDA_SIN_GESTION"
    OPORTUNIDAD_ALTA_PRIORIDAD_PENDIENTE = "OPORTUNIDAD_ALTA_PRIORIDAD_PENDIENTE"
    DESVIO_OBJETIVO_RELEVANTE = "DESVIO_OBJETIVO_RELEVANTE"
    CAMPANIA_EN_EJECUCION_SIN_AVANCE = "CAMPANIA_EN_EJECUCION_SIN_AVANCE"
    SUGERENCIA_CAMPANIA_NO_EJECUTADA = "SUGERENCIA_CAMPANIA_NO_EJECUTADA"


@dataclass(frozen=True, slots=True)
class RiesgoObjetivoSeguro:
    nombre_objetivo: str
    valor_objetivo: float
    valor_proyectado: float
    brecha: float
    estado: str


@dataclass(frozen=True, slots=True)
class AlertaComercialSeguro:
    id_alerta: str
    tipo: TipoAlertaComercialSeguro
    prioridad: PrioridadAlertaSeguro
    regla: ReglaAlertaSeguro
    motivo: str
    accion_sugerida: str
    fecha_objetivo: date | None
    contexto: str
    id_oportunidad: str | None = None


@dataclass(frozen=True, slots=True)
class TrazaResolucionTareaSeguro:
    fecha: datetime
    estado_anterior: EstadoTareaSeguro
    estado_nuevo: EstadoTareaSeguro
    comentario: str


@dataclass(frozen=True, slots=True)
class TareaComercialSeguro:
    id_tarea: str
    tipo: str
    prioridad: PrioridadAlertaSeguro
    motivo: str
    accion_sugerida: str
    fecha_objetivo: date | None
    contexto: str
    estado: EstadoTareaSeguro
    id_oportunidad: str | None = None
    es_alerta_informativa: bool = False
    traza: tuple[TrazaResolucionTareaSeguro, ...] = ()


@dataclass(frozen=True, slots=True)
class AgendaComercialSeguro:
    fecha_corte: date
    prioridades_hoy: tuple[TareaComercialSeguro, ...]
    tareas_vencidas: tuple[TareaComercialSeguro, ...]
    tareas_semana: tuple[TareaComercialSeguro, ...]


@dataclass(frozen=True, slots=True)
class PlanSemanalSeguro:
    agenda: AgendaComercialSeguro
    alertas_activas: tuple[AlertaComercialSeguro, ...]
    riesgos_objetivo: tuple[RiesgoObjetivoSeguro, ...]
    acciones_rapidas: tuple[str, ...]
