from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class EstadoPagoPolizaSeguro(str, Enum):
    AL_DIA = "AL_DIA"
    PROXIMA_A_VENCER = "PROXIMA_A_VENCER"
    VENCIDA = "VENCIDA"
    IMPAGADA = "IMPAGADA"
    EN_REVISION = "EN_REVISION"
    SUSPENDIDA = "SUSPENDIDA"
    REACTIVABLE = "REACTIVABLE"


class EstadoCuotaPolizaSeguro(str, Enum):
    EMITIDA = "EMITIDA"
    PAGADA = "PAGADA"
    VENCIDA = "VENCIDA"
    IMPAGADA = "IMPAGADA"


class NivelRiesgoEconomicoPolizaSeguro(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


@dataclass(frozen=True, slots=True)
class CuotaPolizaSeguro:
    id_cuota: str
    id_poliza: str
    periodo: str
    fecha_emision: date
    fecha_vencimiento: date
    importe: float
    estado: EstadoCuotaPolizaSeguro
    fecha_pago: date | None = None


@dataclass(frozen=True, slots=True)
class VencimientoPolizaSeguro:
    id_poliza: str
    fecha_vencimiento_proxima: date | None
    dias_para_vencer: int | None
    cuotas_vencidas: int


@dataclass(frozen=True, slots=True)
class ImpagoPolizaSeguro:
    id_evento: str
    id_poliza: str
    id_cuota: str
    fecha_evento: date
    motivo: str


@dataclass(frozen=True, slots=True)
class SuspensionPolizaSeguro:
    id_evento: str
    id_poliza: str
    fecha_evento: date
    motivo: str
    automatica: bool


@dataclass(frozen=True, slots=True)
class ReactivacionPolizaSeguro:
    id_evento: str
    id_poliza: str
    fecha_evento: date
    motivo: str


@dataclass(frozen=True, slots=True)
class ResumenEconomicoPolizaSeguro:
    id_poliza: str
    estado_pago: EstadoPagoPolizaSeguro
    nivel_riesgo: NivelRiesgoEconomicoPolizaSeguro
    total_emitido: float
    total_pagado: float
    total_pendiente: float
    cuotas_emitidas: int
    cuotas_pagadas: int
    cuotas_vencidas: int
    cuotas_impagadas: int
    suspendida: bool
    reactivable: bool
    motivo_estado: str


@dataclass(frozen=True, slots=True)
class CarteraEconomicaPolizaSeguro:
    al_dia: tuple[ResumenEconomicoPolizaSeguro, ...]
    proximas_a_vencer: tuple[ResumenEconomicoPolizaSeguro, ...]
    vencidas: tuple[ResumenEconomicoPolizaSeguro, ...]
    impagadas: tuple[ResumenEconomicoPolizaSeguro, ...]
    suspendidas: tuple[ResumenEconomicoPolizaSeguro, ...]
    reactivables: tuple[ResumenEconomicoPolizaSeguro, ...]
