from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import SaludPrediccionDTO


@dataclass(frozen=True, slots=True)
class FiltrosConfirmacionesDTO:
    desde: str
    hasta: str
    texto_paciente: str = ""
    recordatorio_filtro: str = "TODOS"
    riesgo_filtro: str = "TODOS"


@dataclass(frozen=True, slots=True)
class FilaConfirmacionDTO:
    cita_id: int
    inicio: str
    paciente: str
    medico: str
    estado_cita: str
    riesgo: str
    recordatorio_estado: str


@dataclass(frozen=True, slots=True)
class ResultadoConfirmacionesDTO:
    total: int
    mostrados: int
    items: list[FilaConfirmacionDTO]
    salud_prediccion: SaludPrediccionDTO | None = None
