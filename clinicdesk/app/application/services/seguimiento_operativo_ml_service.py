from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from clinicdesk.app.application.telemetria import ahora_utc_iso


class EstadoSeguimientoItemML(str, Enum):
    PENDIENTE = "pendiente"
    REVISADO = "revisado"
    POSPUESTO = "pospuesto"
    DESCARTADO = "descartado"
    RESUELTO = "resuelto"


class AccionHumanaItemML(str, Enum):
    SIN_ACCION = "sin_accion"
    ABRIR_CITA = "abrir_cita"
    CONFIRMAR_CONTACTO = "confirmar_contacto"
    REVISAR_MANUAL = "revisar_manual"


@dataclass(frozen=True, slots=True)
class HistorialDecisionML:
    cita_id: str
    prioridad_ml: str
    accion_sugerida_ml: str
    accion_humana: AccionHumanaItemML
    estado: EstadoSeguimientoItemML
    nota_corta: str
    timestamp_utc: str
    actor: str


@dataclass(frozen=True, slots=True)
class NavegacionObjetivoCitaML:
    cita_id: int
    destino: str
    accion_intent: str


@dataclass(frozen=True, slots=True)
class AccionTomadaML:
    cita_id: str
    prioridad_ml: str
    accion_sugerida_ml: str
    accion_humana: AccionHumanaItemML
    estado: EstadoSeguimientoItemML
    nota_corta: str = ""
    actor: str = "operador"


@dataclass(frozen=True, slots=True)
class ResultadoGestionItemML:
    cita_id: str
    estado_actual: EstadoSeguimientoItemML
    accion_humana_actual: AccionHumanaItemML
    timestamp_utc: str
    historial: tuple[HistorialDecisionML, ...]


class SeguimientoOperativoMLPort(Protocol):
    def registrar_decision(self, decision: HistorialDecisionML) -> None: ...

    def obtener_historial(self, cita_id: str) -> tuple[HistorialDecisionML, ...]: ...


class SeguimientoOperativoMLService:
    _MAX_NOTA = 160

    def __init__(self, repositorio: SeguimientoOperativoMLPort) -> None:
        self._repositorio = repositorio

    def registrar_accion(self, request: AccionTomadaML) -> ResultadoGestionItemML:
        decision = HistorialDecisionML(
            cita_id=request.cita_id,
            prioridad_ml=request.prioridad_ml,
            accion_sugerida_ml=request.accion_sugerida_ml,
            accion_humana=request.accion_humana,
            estado=request.estado,
            nota_corta=self._normalizar_nota(request.nota_corta),
            timestamp_utc=ahora_utc_iso(),
            actor=request.actor.strip() or "operador",
        )
        self._repositorio.registrar_decision(decision)
        historial = self._repositorio.obtener_historial(request.cita_id)
        ultimo = historial[-1]
        return ResultadoGestionItemML(
            cita_id=request.cita_id,
            estado_actual=ultimo.estado,
            accion_humana_actual=ultimo.accion_humana,
            timestamp_utc=ultimo.timestamp_utc,
            historial=historial,
        )

    def obtener_resultado(self, cita_id: str) -> ResultadoGestionItemML | None:
        historial = self._repositorio.obtener_historial(cita_id)
        if not historial:
            return None
        ultimo = historial[-1]
        return ResultadoGestionItemML(
            cita_id=cita_id,
            estado_actual=ultimo.estado,
            accion_humana_actual=ultimo.accion_humana,
            timestamp_utc=ultimo.timestamp_utc,
            historial=historial,
        )

    def construir_objetivo_navegacion(self, cita_id: str) -> NavegacionObjetivoCitaML | None:
        if not cita_id.isdigit():
            return None
        return NavegacionObjetivoCitaML(cita_id=int(cita_id), destino="citas", accion_intent="ABRIR_DETALLE")

    def _normalizar_nota(self, nota: str) -> str:
        texto = nota.strip()
        if len(texto) <= self._MAX_NOTA:
            return texto
        return texto[: self._MAX_NOTA]
