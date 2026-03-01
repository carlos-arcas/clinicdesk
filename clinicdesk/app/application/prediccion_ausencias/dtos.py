from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatosEntrenamientoPrediccion:
    paciente_id: int
    no_vino: int
    dias_antelacion: int


@dataclass(frozen=True, slots=True)
class ResultadoComprobacionDatos:
    citas_validas: int
    minimo_requerido: int
    apto_para_entrenar: bool
    mensaje_clave: str


@dataclass(frozen=True, slots=True)
class PrediccionCitaDTO:
    fecha: str
    hora: str
    paciente: str
    medico: str
    riesgo: str
    explicacion: str


@dataclass(frozen=True, slots=True)
class ResultadoPrevisualizacionPrediccion:
    estado: str
    items: list[PrediccionCitaDTO]
