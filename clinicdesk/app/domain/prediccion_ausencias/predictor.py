from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class NivelRiesgo(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


@dataclass(frozen=True, slots=True)
class RegistroEntrenamiento:
    paciente_id: int
    no_vino: int
    dias_antelacion: int


@dataclass(frozen=True, slots=True)
class CitaParaPrediccion:
    cita_id: int
    paciente_id: int
    dias_antelacion: int


@dataclass(frozen=True, slots=True)
class PrediccionAusencia:
    cita_id: int
    riesgo: NivelRiesgo
    explicacion_corta: str


class PredictorEntrenado(Protocol):
    def predecir(self, citas: list[CitaParaPrediccion]) -> list[PrediccionAusencia]:
        ...


class PredictorAusencias(Protocol):
    def entrenar(self, dataset: list[RegistroEntrenamiento]) -> PredictorEntrenado:
        ...
