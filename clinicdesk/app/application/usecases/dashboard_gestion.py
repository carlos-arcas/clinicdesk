from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from clinicdesk.app.application.usecases.dashboard_gestion_prediccion import (
    CitaVigilarDTO,
    EstadosPrediccionDashboardDTO,
    ListarCitasHoyGestionPort,
    PrediccionAusenciasPort,
    PrediccionOperativaPort,
    resolver_citas_a_vigilar,
    resolver_estados_prediccion,
)
from clinicdesk.app.application.usecases.obtener_metricas_operativas import KpiMedicoDTO, ResultadoMetricasOperativasDTO
from clinicdesk.app.domain.exceptions import ValidationError

PRESET_HOY = "HOY"
PRESET_7_DIAS = "7_DIAS"
PRESET_30_DIAS = "30_DIAS"
PRESET_PERSONALIZADO = "PERSONALIZADO"
PRESETS_VALIDOS = {PRESET_HOY, PRESET_7_DIAS, PRESET_30_DIAS, PRESET_PERSONALIZADO}
MAX_DIAS_RANGO_DASHBOARD = 90
TOP_MEDICOS_LIMITE = 5
UMBRAL_ALERTA_ESPERA_ALTA_MIN = 15.0
UMBRAL_ALERTA_RETRASO_ALTO_MIN = 10.0
UMBRAL_ALERTA_POCOS_DATOS_ESPERA = 20


@dataclass(frozen=True, slots=True)
class FiltrosDashboardDTO:
    preset: str = PRESET_7_DIAS
    desde: date | None = None
    hasta: date | None = None


@dataclass(frozen=True, slots=True)
class KpisResumenDashboardDTO:
    total_citas: int
    espera_media_min: float | None
    duracion_media_consulta_min: float | None
    retraso_media_min: float | None
    total_validas_espera: int


@dataclass(frozen=True, slots=True)
class TopMedicoDashboardDTO:
    medico_nombre: str
    total_citas: int
    espera_media_min: float | None
    duracion_media_consulta_min: float | None
    retraso_media_min: float | None


@dataclass(frozen=True, slots=True)
class AlertaDashboardDTO:
    code: str
    i18n_key: str
    severidad: str


@dataclass(frozen=True, slots=True)
class DashboardGestionDTO:
    desde: str
    hasta: str
    kpis_resumen: KpisResumenDashboardDTO
    top_medicos: tuple[TopMedicoDashboardDTO, ...]
    alertas: tuple[AlertaDashboardDTO, ...]
    estados_prediccion: EstadosPrediccionDashboardDTO
    citas_a_vigilar: tuple[CitaVigilarDTO, ...]


class ObtenerMetricasOperativasPort(Protocol):
    def execute(self, desde: date, hasta: date) -> ResultadoMetricasOperativasDTO:
        ...


class ObtenerDashboardGestion:
    def __init__(
        self,
        obtener_metricas_operativas: ObtenerMetricasOperativasPort,
        prediccion_ausencias: PrediccionAusenciasPort,
        prediccion_operativa: PrediccionOperativaPort,
        citas_hoy_queries: ListarCitasHoyGestionPort,
    ) -> None:
        self._obtener_metricas_operativas = obtener_metricas_operativas
        self._prediccion_ausencias = prediccion_ausencias
        self._prediccion_operativa = prediccion_operativa
        self._citas_hoy_queries = citas_hoy_queries

    def execute(self, filtros: FiltrosDashboardDTO, hoy: date | None = None) -> DashboardGestionDTO:
        hoy_ref = hoy or date.today()
        filtros_norm = normalizar_filtros_dashboard(filtros, hoy_ref)
        metricas = self._obtener_metricas_operativas.execute(filtros_norm.desde, filtros_norm.hasta)
        kpis = _derivar_kpis_resumen(metricas)
        return DashboardGestionDTO(
            desde=filtros_norm.desde.isoformat(),
            hasta=filtros_norm.hasta.isoformat(),
            kpis_resumen=kpis,
            top_medicos=_derivar_top_medicos(metricas.por_medico),
            alertas=_derivar_alertas(kpis),
            estados_prediccion=resolver_estados_prediccion(self._prediccion_ausencias, self._prediccion_operativa),
            citas_a_vigilar=resolver_citas_a_vigilar(
                self._citas_hoy_queries,
                self._prediccion_ausencias,
                self._prediccion_operativa,
            ),
        )


def normalizar_filtros_dashboard(filtros: FiltrosDashboardDTO, hoy: date) -> FiltrosDashboardDTO:
    preset = _normalizar_preset(filtros.preset)
    desde, hasta = _resolver_rango(preset, filtros.desde, filtros.hasta, hoy)
    _validar_rango_maximo(desde, hasta)
    return FiltrosDashboardDTO(preset=preset, desde=desde, hasta=hasta)


def _normalizar_preset(preset: str | None) -> str:
    valor = (preset or "").strip().upper()
    return valor if valor in PRESETS_VALIDOS else PRESET_7_DIAS


def _resolver_rango(preset: str, desde: date | None, hasta: date | None, hoy: date) -> tuple[date, date]:
    if preset == PRESET_HOY:
        return hoy, hoy
    if preset == PRESET_30_DIAS:
        return hoy - timedelta(days=29), hoy
    if preset == PRESET_PERSONALIZADO and desde and hasta:
        return (desde, hasta) if desde <= hasta else (hasta, desde)
    return hoy - timedelta(days=6), hoy


def _validar_rango_maximo(desde: date, hasta: date) -> None:
    dias_inclusivos = (hasta - desde).days + 1
    if dias_inclusivos > MAX_DIAS_RANGO_DASHBOARD:
        raise ValidationError("El rango máximo del dashboard es de 90 días.")


def _derivar_kpis_resumen(metricas: ResultadoMetricasOperativasDTO) -> KpisResumenDashboardDTO:
    total_citas = sum(dia.total_citas for dia in metricas.por_dia)
    total_validas_espera = sum(dia.total_validas_espera for dia in metricas.por_dia)
    return KpisResumenDashboardDTO(
        total_citas=total_citas,
        espera_media_min=_promedio_ponderado(metricas.por_dia, "espera_media_min", "total_validas_espera"),
        duracion_media_consulta_min=_promedio_ponderado(metricas.por_dia, "consulta_media_min", "total_validas_consulta"),
        retraso_media_min=_promedio_ponderado(metricas.por_dia, "retraso_media_min", "total_validas_retraso"),
        total_validas_espera=total_validas_espera,
    )


def _promedio_ponderado(filas: tuple, campo_media: str, campo_total: str) -> float | None:
    suma = 0.0
    total = 0
    for fila in filas:
        media = getattr(fila, campo_media)
        cantidad = getattr(fila, campo_total)
        if media is None or cantidad <= 0:
            continue
        suma += media * cantidad
        total += cantidad
    if total == 0:
        return None
    return round(suma / total, 2)


def _derivar_top_medicos(por_medico: tuple[KpiMedicoDTO, ...]) -> tuple[TopMedicoDashboardDTO, ...]:
    medicos_ordenados = sorted(por_medico, key=lambda fila: (-fila.total_citas, fila.medico_nombre.casefold()))
    top = medicos_ordenados[:TOP_MEDICOS_LIMITE]
    return tuple(
        TopMedicoDashboardDTO(
            medico_nombre=fila.medico_nombre,
            total_citas=fila.total_citas,
            espera_media_min=fila.espera_media_min,
            duracion_media_consulta_min=fila.consulta_media_min,
            retraso_media_min=fila.retraso_media_min,
        )
        for fila in top
    )


def _derivar_alertas(kpis: KpisResumenDashboardDTO) -> tuple[AlertaDashboardDTO, ...]:
    alertas: list[AlertaDashboardDTO] = []
    if (kpis.espera_media_min or 0.0) > UMBRAL_ALERTA_ESPERA_ALTA_MIN:
        alertas.append(_build_alerta("espera_alta", "dashboard_gestion.alerta.espera_alta", "MEDIA"))
    if (kpis.retraso_media_min or 0.0) > UMBRAL_ALERTA_RETRASO_ALTO_MIN:
        alertas.append(_build_alerta("retraso_alto", "dashboard_gestion.alerta.retraso_alto", "MEDIA"))
    if kpis.total_validas_espera < UMBRAL_ALERTA_POCOS_DATOS_ESPERA:
        alertas.append(_build_alerta("pocos_datos", "dashboard_gestion.alerta.pocos_datos", "SUAVE"))
    return tuple(alertas)


def _build_alerta(code: str, i18n_key: str, severidad: str) -> AlertaDashboardDTO:
    return AlertaDashboardDTO(code=code, i18n_key=i18n_key, severidad=severidad)
