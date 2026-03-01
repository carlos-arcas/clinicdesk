from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DatosRecordatorioCitaDTO:
    cita_id: int
    inicio: str
    paciente_nombre: str
    telefono: str | None
    email: str | None
    medico_nombre: str | None


@dataclass(frozen=True, slots=True)
class RecordatorioPreviewDTO:
    canal: str
    mensaje: str
    advertencias: tuple[str, ...]
    puede_copiar: bool


@dataclass(frozen=True, slots=True)
class EstadoRecordatorioDTO:
    canal: str
    estado: str
    updated_at_utc: str


class RecordatoriosCitasPort(Protocol):
    def obtener_datos_recordatorio_cita(self, cita_id: int) -> DatosRecordatorioCitaDTO | None:
        ...

    def upsert_recordatorio_cita(self, cita_id: int, canal: str, estado: str, now_utc: str) -> None:
        ...

    def obtener_estado_recordatorio(self, cita_id: int) -> tuple[EstadoRecordatorioDTO, ...]:
        ...
