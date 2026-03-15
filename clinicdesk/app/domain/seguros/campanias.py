from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum


class EstadoCampaniaSeguro(str, Enum):
    CREADA = "CREADA"
    EN_EJECUCION = "EN_EJECUCION"
    CERRADA = "CERRADA"


class OrigenCampaniaSeguro(str, Enum):
    COHORTE = "COHORTE"
    CRITERIO = "CRITERIO"
    SUGERENCIA = "SUGERENCIA"


class EstadoItemCampaniaSeguro(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONTACTADO = "CONTACTADO"
    EN_REVISION = "EN_REVISION"
    CONVERTIDO = "CONVERTIDO"
    RECHAZADO = "RECHAZADO"
    POSPUESTO = "POSPUESTO"


class ResultadoItemCampaniaSeguro(str, Enum):
    SIN_RESULTADO = "SIN_RESULTADO"
    CONTACTO_LOGRADO = "CONTACTO_LOGRADO"
    REVISION_AGENDADA = "REVISION_AGENDADA"
    CONVERSION = "CONVERSION"
    RECHAZO = "RECHAZO"
    POSPOSICION = "POSPOSICION"


@dataclass(frozen=True, slots=True)
class CriterioCampaniaSeguro:
    origen: OrigenCampaniaSeguro
    descripcion: str
    id_referencia: str | None


@dataclass(frozen=True, slots=True)
class ItemCampaniaSeguro:
    id_item: str
    id_campania: str
    id_oportunidad: str
    estado_trabajo: EstadoItemCampaniaSeguro
    accion_tomada: str
    resultado: ResultadoItemCampaniaSeguro
    nota_corta: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ResultadoCampaniaSeguro:
    total_items: int
    trabajados: int
    convertidos: int
    rechazados: int
    pendientes: int
    ratio_conversion: float
    ratio_avance: float


@dataclass(frozen=True, slots=True)
class CampaniaSeguro:
    id_campania: str
    nombre: str
    objetivo_comercial: str
    creado_en: datetime
    criterio: CriterioCampaniaSeguro
    tamano_lote: int
    estado: EstadoCampaniaSeguro
    resultado_agregado: ResultadoCampaniaSeguro

    def iniciar(self) -> CampaniaSeguro:
        if self.estado is not EstadoCampaniaSeguro.CREADA:
            raise ValueError("La campaña solo puede iniciar desde estado CREADA")
        return replace(self, estado=EstadoCampaniaSeguro.EN_EJECUCION)

    def cerrar(self, resultado: ResultadoCampaniaSeguro) -> CampaniaSeguro:
        if self.estado is EstadoCampaniaSeguro.CERRADA:
            raise ValueError("La campaña ya está cerrada")
        return replace(self, estado=EstadoCampaniaSeguro.CERRADA, resultado_agregado=resultado)


def crear_resultado_vacio(total_items: int) -> ResultadoCampaniaSeguro:
    return ResultadoCampaniaSeguro(
        total_items=total_items,
        trabajados=0,
        convertidos=0,
        rechazados=0,
        pendientes=total_items,
        ratio_conversion=0.0,
        ratio_avance=0.0,
    )


def reconstruir_resultado(items: tuple[ItemCampaniaSeguro, ...]) -> ResultadoCampaniaSeguro:
    total = len(items)
    trabajados = sum(1 for item in items if item.resultado is not ResultadoItemCampaniaSeguro.SIN_RESULTADO)
    convertidos = sum(1 for item in items if item.resultado is ResultadoItemCampaniaSeguro.CONVERSION)
    rechazados = sum(1 for item in items if item.resultado is ResultadoItemCampaniaSeguro.RECHAZO)
    pendientes = total - trabajados
    ratio_conversion = (convertidos / trabajados) if trabajados else 0.0
    ratio_avance = (trabajados / total) if total else 0.0
    return ResultadoCampaniaSeguro(
        total, trabajados, convertidos, rechazados, pendientes, ratio_conversion, ratio_avance
    )


def nuevo_item_campania(id_campania: str, id_oportunidad: str, posicion: int) -> ItemCampaniaSeguro:
    return ItemCampaniaSeguro(
        id_item=f"{id_campania}-item-{posicion}",
        id_campania=id_campania,
        id_oportunidad=id_oportunidad,
        estado_trabajo=EstadoItemCampaniaSeguro.PENDIENTE,
        accion_tomada="-",
        resultado=ResultadoItemCampaniaSeguro.SIN_RESULTADO,
        nota_corta="-",
        timestamp=datetime.now(tz=UTC),
    )
