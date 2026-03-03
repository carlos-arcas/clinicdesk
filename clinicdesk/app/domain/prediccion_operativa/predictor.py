from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class NivelRiesgo(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    NO_DISPONIBLE = "NO_DISPONIBLE"


@dataclass(frozen=True, slots=True)
class RegistroOperativo:
    medico_id: int
    tipo_cita: str | None
    franja_hora: str | None
    dia_semana: int | None
    minutos: float


@dataclass(frozen=True, slots=True)
class CitaOperativa:
    cita_id: int
    medico_id: int
    tipo_cita: str | None
    franja_hora: str | None
    dia_semana: int | None


@dataclass(frozen=True, slots=True)
class PrediccionOperativa:
    cita_id: int
    nivel: NivelRiesgo
    reason_codes: tuple[str, ...]


class ModeloOperativo(Protocol):
    def predecir(self, citas: list[CitaOperativa]) -> list[PrediccionOperativa]: ...


class PredictorOperativo(Protocol):
    def entrenar(self, dataset: list[RegistroOperativo]) -> ModeloOperativo: ...
