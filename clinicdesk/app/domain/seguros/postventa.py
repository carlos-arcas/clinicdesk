from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class EstadoPolizaSeguro(str, Enum):
    ACTIVA = "ACTIVA"
    RENOVADA = "RENOVADA"
    NO_RENOVADA = "NO_RENOVADA"
    CANCELADA = "CANCELADA"


class EstadoAseguradoSeguro(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class EstadoRenovacionPolizaSeguro(str, Enum):
    PENDIENTE = "PENDIENTE"
    RENOVADA = "RENOVADA"
    NO_RENOVADA = "NO_RENOVADA"
    CANCELADA = "CANCELADA"


class TipoIncidenciaPolizaSeguro(str, Enum):
    ADMINISTRATIVA = "ADMINISTRATIVA"
    REVISION_COBERTURA = "REVISION_COBERTURA"
    DOCUMENTACION_PENDIENTE = "DOCUMENTACION_PENDIENTE"
    RENOVACION_BLOQUEADA = "RENOVACION_BLOQUEADA"
    ESTADO_IRREGULAR = "ESTADO_IRREGULAR"


class EstadoIncidenciaPolizaSeguro(str, Enum):
    ABIERTA = "ABIERTA"
    EN_REVISION = "EN_REVISION"
    CERRADA = "CERRADA"


@dataclass(frozen=True, slots=True)
class AseguradoPrincipalSeguro:
    id_asegurado: str
    nombre: str
    documento: str
    estado: EstadoAseguradoSeguro


@dataclass(frozen=True, slots=True)
class BeneficiarioSeguro:
    id_beneficiario: str
    nombre: str
    parentesco: str
    estado: EstadoAseguradoSeguro


@dataclass(frozen=True, slots=True)
class VigenciaPolizaSeguro:
    fecha_inicio: date
    fecha_fin: date


@dataclass(frozen=True, slots=True)
class RenovacionPolizaSeguro:
    fecha_renovacion_prevista: date
    estado: EstadoRenovacionPolizaSeguro


@dataclass(frozen=True, slots=True)
class IncidenciaPolizaSeguro:
    id_incidencia: str
    tipo: TipoIncidenciaPolizaSeguro
    descripcion: str
    estado: EstadoIncidenciaPolizaSeguro
    fecha_apertura: date


@dataclass(frozen=True, slots=True)
class CoberturaActivaPolizaSeguro:
    codigo_cobertura: str
    descripcion: str
    activa: bool


@dataclass(frozen=True, slots=True)
class PolizaSeguro:
    id_poliza: str
    id_oportunidad_origen: str
    id_paciente: str
    id_plan: str
    estado: EstadoPolizaSeguro
    titular: AseguradoPrincipalSeguro
    beneficiarios: tuple[BeneficiarioSeguro, ...]
    vigencia: VigenciaPolizaSeguro
    renovacion: RenovacionPolizaSeguro
    coberturas: tuple[CoberturaActivaPolizaSeguro, ...]
    incidencias: tuple[IncidenciaPolizaSeguro, ...]
