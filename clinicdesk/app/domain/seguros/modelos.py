from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TipoPlanSeguro(str, Enum):
    CLINICA = "CLINICA"
    EXTERNO = "EXTERNO"


class EstadoElegibilidadSeguro(str, Enum):
    ELEGIBLE = "ELEGIBLE"
    ELEGIBLE_CON_REVISION = "ELEGIBLE_CON_REVISION"
    NO_ELEGIBLE = "NO_ELEGIBLE"
    INFORMACION_INSUFICIENTE = "INFORMACION_INSUFICIENTE"


@dataclass(frozen=True, slots=True)
class CoberturaSeguro:
    codigo: str
    nombre: str
    incluida: bool
    observacion: str = ""


@dataclass(frozen=True, slots=True)
class CarenciaSeguro:
    codigo: str
    meses: int


@dataclass(frozen=True, slots=True)
class CopagoSeguro:
    codigo: str
    importe_fijo: float


@dataclass(frozen=True, slots=True)
class LimiteSeguro:
    codigo: str
    maximo_anual: int


@dataclass(frozen=True, slots=True)
class ExclusionSeguro:
    codigo: str
    descripcion: str


@dataclass(frozen=True, slots=True)
class ReglaElegibilidadSeguro:
    codigo: str
    campo: str
    valor_requerido: str
    obligatoria: bool
    motivo: str


@dataclass(frozen=True, slots=True)
class PlanSeguro:
    id_plan: str
    nombre: str
    tipo_plan: TipoPlanSeguro
    cuota_mensual: float
    coberturas: tuple[CoberturaSeguro, ...]
    carencias: tuple[CarenciaSeguro, ...]
    copagos: tuple[CopagoSeguro, ...]
    limites: tuple[LimiteSeguro, ...]
    exclusiones: tuple[ExclusionSeguro, ...]
    reglas_elegibilidad: tuple[ReglaElegibilidadSeguro, ...]


@dataclass(frozen=True, slots=True)
class ProductoExternoComparable:
    id_producto: str
    nombre: str
    proveedor: str
    plan_base: PlanSeguro


@dataclass(frozen=True, slots=True)
class PerfilCandidatoSeguro:
    edad: int | None
    residencia_pais: str | None
    historial_impagos: bool | None
    preexistencias_graves: bool | None


@dataclass(frozen=True, slots=True)
class ResultadoElegibilidadSeguro:
    estado: EstadoElegibilidadSeguro
    razones: tuple[str, ...]
    campos_faltantes: tuple[str, ...]
