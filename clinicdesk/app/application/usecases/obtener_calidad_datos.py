from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from clinicdesk.app.queries.calidad_datos_queries import FaltantesCalidadDatos

UMBRAL_PCT_COMPLETAS_REVISION = 60.0
UMBRAL_FALTANTES_INICIO_FIN = 20
UMBRAL_FALTANTES_CHECKS = 20


@dataclass(frozen=True, slots=True)
class AlertaDTO:
    code: str
    i18n_key: str
    severidad: str


@dataclass(frozen=True, slots=True)
class CalidadDatosDTO:
    total_cerradas: int
    completas: int
    pct_completas: float
    faltan_check_in: int
    faltan_inicio_fin: int
    faltan_check_out: int
    alertas: tuple[AlertaDTO, ...]


class CalidadDatosPort(Protocol):
    def contar_citas_cerradas(self, desde: date, hasta: date) -> int: ...

    def contar_completas(self, desde: date, hasta: date) -> int: ...

    def contar_faltantes(self, desde: date, hasta: date) -> FaltantesCalidadDatos: ...


class ObtenerCalidadDatos:
    def __init__(self, queries: CalidadDatosPort) -> None:
        self._queries = queries

    def execute(self, desde: date, hasta: date) -> CalidadDatosDTO:
        total_cerradas = self._queries.contar_citas_cerradas(desde, hasta)
        completas = self._queries.contar_completas(desde, hasta)
        faltantes = self._queries.contar_faltantes(desde, hasta)
        pct_completas = _calcular_porcentaje_completas(completas, total_cerradas)
        alertas = _derivar_alertas(pct_completas, faltantes)
        return CalidadDatosDTO(
            total_cerradas=total_cerradas,
            completas=completas,
            pct_completas=pct_completas,
            faltan_check_in=faltantes.faltan_check_in,
            faltan_inicio_fin=faltantes.faltan_inicio_fin,
            faltan_check_out=faltantes.faltan_check_out,
            alertas=alertas,
        )


def _calcular_porcentaje_completas(completas: int, total_cerradas: int) -> float:
    if total_cerradas <= 0:
        return 0.0
    return round((completas * 100.0) / total_cerradas, 2)


def _derivar_alertas(pct_completas: float, faltantes: FaltantesCalidadDatos) -> tuple[AlertaDTO, ...]:
    alertas: list[AlertaDTO] = []
    if pct_completas < UMBRAL_PCT_COMPLETAS_REVISION:
        alertas.append(AlertaDTO("revision_calidad", "dashboard_gestion.calidad.alerta.revision", "MEDIA"))
    if faltantes.faltan_inicio_fin > UMBRAL_FALTANTES_INICIO_FIN:
        alertas.append(AlertaDTO("faltan_inicio_fin", "dashboard_gestion.calidad.alerta.inicio_fin", "ALTA"))
    if _faltan_checks_altos(faltantes):
        alertas.append(AlertaDTO("faltan_checks", "dashboard_gestion.calidad.alerta.checks", "MEDIA"))
    return tuple(alertas)


def _faltan_checks_altos(faltantes: FaltantesCalidadDatos) -> bool:
    return (faltantes.faltan_check_in > UMBRAL_FALTANTES_CHECKS) or (
        faltantes.faltan_check_out > UMBRAL_FALTANTES_CHECKS
    )
