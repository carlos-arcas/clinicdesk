from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import Enum


class EstadoOportunidadSeguro(str, Enum):
    DETECTADA = "DETECTADA"
    ANALIZADA = "ANALIZADA"
    ELEGIBLE = "ELEGIBLE"
    OFERTA_PREPARADA = "OFERTA_PREPARADA"
    OFERTA_ENVIADA = "OFERTA_ENVIADA"
    EN_SEGUIMIENTO = "EN_SEGUIMIENTO"
    CONVERTIDA = "CONVERTIDA"
    RECHAZADA = "RECHAZADA"
    POSPUESTA = "POSPUESTA"
    PENDIENTE_RENOVACION = "PENDIENTE_RENOVACION"
    RENOVADA = "RENOVADA"
    NO_RENOVADA = "NO_RENOVADA"


class ResultadoComercialSeguro(str, Enum):
    CONVERTIDO = "CONVERTIDO"
    RECHAZADO = "RECHAZADO"
    POSPUESTO = "POSPUESTO"
    PENDIENTE_REVISION = "PENDIENTE_REVISION"


class ResultadoRenovacionSeguro(str, Enum):
    PENDIENTE = "PENDIENTE"
    RENOVADA = "RENOVADA"
    NO_RENOVADA = "NO_RENOVADA"


@dataclass(frozen=True, slots=True)
class CandidatoSeguro:
    id_candidato: str
    id_paciente: str
    segmento: str


@dataclass(frozen=True, slots=True)
class OfertaSeguro:
    id_oferta: str
    id_oportunidad: str
    plan_propuesto_id: str
    resumen_valor: str
    puntos_fuertes: tuple[str, ...]
    riesgos_revision: tuple[str, ...]
    clasificacion_migracion: str
    notas_comerciales: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SeguimientoOportunidadSeguro:
    fecha_registro: datetime
    estado: EstadoOportunidadSeguro
    accion_comercial: str
    nota_corta: str
    siguiente_paso: str


@dataclass(frozen=True, slots=True)
class RenovacionSeguro:
    id_renovacion: str
    id_oportunidad: str
    plan_vigente_id: str
    fecha_renovacion: date
    revision_pendiente: bool
    resultado: ResultadoRenovacionSeguro


@dataclass(frozen=True, slots=True)
class OportunidadSeguro:
    id_oportunidad: str
    candidato: CandidatoSeguro
    plan_origen_id: str
    plan_destino_id: str
    estado_actual: EstadoOportunidadSeguro
    clasificacion_motor: str
    seguimientos: tuple[SeguimientoOportunidadSeguro, ...]
    resultado_comercial: ResultadoComercialSeguro | None

    def cambiar_estado(self, nuevo_estado: EstadoOportunidadSeguro) -> OportunidadSeguro:
        validar_transicion_estado(self.estado_actual, nuevo_estado)
        return replace(self, estado_actual=nuevo_estado)

    def agregar_seguimiento(self, seguimiento: SeguimientoOportunidadSeguro) -> OportunidadSeguro:
        validar_transicion_estado(self.estado_actual, seguimiento.estado)
        return replace(self, estado_actual=seguimiento.estado, seguimientos=self.seguimientos + (seguimiento,))


_TRANSICIONES_ESTADO: dict[EstadoOportunidadSeguro, set[EstadoOportunidadSeguro]] = {
    EstadoOportunidadSeguro.DETECTADA: {EstadoOportunidadSeguro.ANALIZADA},
    EstadoOportunidadSeguro.ANALIZADA: {EstadoOportunidadSeguro.ELEGIBLE, EstadoOportunidadSeguro.RECHAZADA},
    EstadoOportunidadSeguro.ELEGIBLE: {EstadoOportunidadSeguro.OFERTA_PREPARADA, EstadoOportunidadSeguro.RECHAZADA},
    EstadoOportunidadSeguro.OFERTA_PREPARADA: {EstadoOportunidadSeguro.OFERTA_ENVIADA},
    EstadoOportunidadSeguro.OFERTA_ENVIADA: {
        EstadoOportunidadSeguro.EN_SEGUIMIENTO,
        EstadoOportunidadSeguro.CONVERTIDA,
        EstadoOportunidadSeguro.RECHAZADA,
        EstadoOportunidadSeguro.POSPUESTA,
    },
    EstadoOportunidadSeguro.EN_SEGUIMIENTO: {
        EstadoOportunidadSeguro.CONVERTIDA,
        EstadoOportunidadSeguro.RECHAZADA,
        EstadoOportunidadSeguro.POSPUESTA,
    },
    EstadoOportunidadSeguro.CONVERTIDA: {EstadoOportunidadSeguro.PENDIENTE_RENOVACION},
    EstadoOportunidadSeguro.PENDIENTE_RENOVACION: {
        EstadoOportunidadSeguro.RENOVADA,
        EstadoOportunidadSeguro.NO_RENOVADA,
    },
    EstadoOportunidadSeguro.RECHAZADA: set(),
    EstadoOportunidadSeguro.POSPUESTA: {EstadoOportunidadSeguro.EN_SEGUIMIENTO, EstadoOportunidadSeguro.RECHAZADA},
    EstadoOportunidadSeguro.RENOVADA: set(),
    EstadoOportunidadSeguro.NO_RENOVADA: set(),
}


def validar_transicion_estado(estado_actual: EstadoOportunidadSeguro, nuevo_estado: EstadoOportunidadSeguro) -> None:
    if nuevo_estado == estado_actual:
        return
    destinos = _TRANSICIONES_ESTADO.get(estado_actual, set())
    if nuevo_estado not in destinos:
        msg = f"Transicion invalida para oportunidad seguro: {estado_actual.value} -> {nuevo_estado.value}"
        raise ValueError(msg)
