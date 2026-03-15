from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class TipoItemColaSeguro(str, Enum):
    OPORTUNIDAD = "OPORTUNIDAD"
    RENOVACION = "RENOVACION"
    SEGUIMIENTO_VENCIDO = "SEGUIMIENTO_VENCIDO"


class PrioridadTrabajoSeguro(str, Enum):
    MUY_PRIORITARIA = "MUY_PRIORITARIA"
    PRIORITARIA = "PRIORITARIA"
    SECUNDARIA = "SECUNDARIA"
    NO_PRIORITARIA = "NO_PRIORITARIA"


class EstadoOperativoSeguro(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    POSPUESTO = "POSPUESTO"
    PENDIENTE_DOCUMENTACION = "PENDIENTE_DOCUMENTACION"
    RESUELTO = "RESUELTO"
    DESCARTADO = "DESCARTADO"


class AccionPendienteSeguro(str, Enum):
    REVISADO = "REVISADO"
    CONTACTADO = "CONTACTADO"
    SEGUIMIENTO_REALIZADO = "SEGUIMIENTO_REALIZADO"
    POSPUESTO = "POSPUESTO"
    PENDIENTE_DOCUMENTACION = "PENDIENTE_DOCUMENTACION"
    RESUELTO = "RESUELTO"
    DESCARTADO = "DESCARTADO"


@dataclass(frozen=True, slots=True)
class RecordatorioSeguimientoSeguro:
    fecha_objetivo: date
    vencido: bool
    dias_desfase: int


@dataclass(frozen=True, slots=True)
class GestionOperativaColaSeguro:
    id_oportunidad: str
    accion: AccionPendienteSeguro
    estado_resultante: EstadoOperativoSeguro
    nota_corta: str
    siguiente_paso: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ItemColaComercialSeguro:
    id_oportunidad: str
    tipo_item: TipoItemColaSeguro
    prioridad: PrioridadTrabajoSeguro
    motivo_principal: str
    siguiente_accion_sugerida: str
    estado_operativo: EstadoOperativoSeguro
    riesgo_cautela: str
    plan_contexto: str
    score_prioridad: float
    recordatorio: RecordatorioSeguimientoSeguro | None
    ultima_gestion: GestionOperativaColaSeguro | None


@dataclass(frozen=True, slots=True)
class ColaTrabajoSeguro:
    fecha_corte: datetime
    items: tuple[ItemColaComercialSeguro, ...]

    def filtrar_por_estado(self, estado: EstadoOperativoSeguro) -> tuple[ItemColaComercialSeguro, ...]:
        return tuple(item for item in self.items if item.estado_operativo is estado)

    def filtrar_vencidas(self) -> tuple[ItemColaComercialSeguro, ...]:
        return tuple(item for item in self.items if item.recordatorio and item.recordatorio.vencido)

    def filtrar_renovaciones(self) -> tuple[ItemColaComercialSeguro, ...]:
        return tuple(item for item in self.items if item.tipo_item is TipoItemColaSeguro.RENOVACION)

    def filtrar_alta_prioridad(self) -> tuple[ItemColaComercialSeguro, ...]:
        return tuple(
            item
            for item in self.items
            if item.prioridad in {PrioridadTrabajoSeguro.MUY_PRIORITARIA, PrioridadTrabajoSeguro.PRIORITARIA}
        )


@dataclass(frozen=True, slots=True)
class ResultadoGestionColaSeguro:
    id_oportunidad: str
    estado_operativo: EstadoOperativoSeguro
    accion_registrada: AccionPendienteSeguro
    timestamp: datetime


_MAPA_ESTADO_ACCION: dict[AccionPendienteSeguro, EstadoOperativoSeguro] = {
    AccionPendienteSeguro.REVISADO: EstadoOperativoSeguro.EN_CURSO,
    AccionPendienteSeguro.CONTACTADO: EstadoOperativoSeguro.EN_CURSO,
    AccionPendienteSeguro.SEGUIMIENTO_REALIZADO: EstadoOperativoSeguro.EN_CURSO,
    AccionPendienteSeguro.POSPUESTO: EstadoOperativoSeguro.POSPUESTO,
    AccionPendienteSeguro.PENDIENTE_DOCUMENTACION: EstadoOperativoSeguro.PENDIENTE_DOCUMENTACION,
    AccionPendienteSeguro.RESUELTO: EstadoOperativoSeguro.RESUELTO,
    AccionPendienteSeguro.DESCARTADO: EstadoOperativoSeguro.DESCARTADO,
}


def estado_resultante_por_accion(accion: AccionPendienteSeguro) -> EstadoOperativoSeguro:
    return _MAPA_ESTADO_ACCION[accion]
