from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from clinicdesk.app.application.seguros.agenda_alertas_contratos import TareaComercialSeguro


@dataclass(frozen=True, slots=True)
class PeriodoSemanaSeguro:
    fecha_inicio: date
    fecha_fin: date
    fecha_corte: date


@dataclass(frozen=True, slots=True)
class CumplimientoPlanSeguro:
    periodo: PeriodoSemanaSeguro
    tareas_previstas: tuple[TareaComercialSeguro, ...]
    tareas_ejecutadas: tuple[TareaComercialSeguro, ...]
    tareas_pendientes: tuple[TareaComercialSeguro, ...]
    tareas_vencidas: tuple[TareaComercialSeguro, ...]
    tareas_criticas_no_ejecutadas: tuple[TareaComercialSeguro, ...]
    porcentaje_cumplimiento: float


@dataclass(frozen=True, slots=True)
class DesvioEjecucionSeguro:
    periodo: PeriodoSemanaSeguro
    codigo: str
    severidad: str
    descripcion: str
    impacto: str
    accion_recomendada: str


@dataclass(frozen=True, slots=True)
class BloqueoOperativoSeguro:
    periodo: PeriodoSemanaSeguro
    codigo: str
    descripcion: str
    evidencia: str
    accion_desbloqueo: str


@dataclass(frozen=True, slots=True)
class AprendizajeEjecucionSeguro:
    periodo: PeriodoSemanaSeguro
    tareas_que_avanzan: tuple[str, ...]
    tareas_que_se_atrasan: tuple[str, ...]
    acciones_con_mayor_avance: tuple[str, ...]
    zonas_atasco: tuple[str, ...]
    recomendacion_semana_siguiente: str


@dataclass(frozen=True, slots=True)
class CierreSemanalSeguro:
    periodo: PeriodoSemanaSeguro
    tareas_previstas: tuple[TareaComercialSeguro, ...]
    tareas_ejecutadas: tuple[TareaComercialSeguro, ...]
    tareas_pendientes: tuple[TareaComercialSeguro, ...]
    tareas_vencidas: tuple[TareaComercialSeguro, ...]
    bloqueos: tuple[BloqueoOperativoSeguro, ...]
    patrones: tuple[str, ...]
    recomendacion_semana_siguiente: str


@dataclass(frozen=True, slots=True)
class ResumenSemanaSeguro:
    cierre: CierreSemanalSeguro
    cumplimiento: CumplimientoPlanSeguro
    desvios: tuple[DesvioEjecucionSeguro, ...]
    bloqueos: tuple[BloqueoOperativoSeguro, ...]
    aprendizaje: AprendizajeEjecucionSeguro
