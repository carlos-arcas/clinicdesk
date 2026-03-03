from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResultadoComprobacionOperativa:
    ejemplos_validos: int
    minimo_requerido: int
    apto_para_entrenar: bool


@dataclass(frozen=True, slots=True)
class ResultadoEntrenamientoOperativo:
    ejemplos_usados: int
    fecha_entrenamiento: str


@dataclass(frozen=True, slots=True)
class PrediccionOperativaDTO:
    cita_id: int
    nivel: str


@dataclass(frozen=True, slots=True)
class SaludPrediccionOperativaDTO:
    estado: str
    fecha_ultima_actualizacion: str | None
    citas_validas_recientes: int


@dataclass(frozen=True, slots=True)
class ExplicacionOperativaDTO:
    nivel: str
    motivos_i18n_keys: tuple[str, ...]
    acciones_i18n_keys: tuple[str, ...]
    necesita_entrenar: bool
