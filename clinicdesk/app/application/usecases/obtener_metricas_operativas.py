from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.queries.metricas_operativas_queries import KpiDiaRow, KpiMedicoRow


LOGGER = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class KpiDiaDTO:
    fecha: str
    total_citas: int
    espera_media_min: float | None
    consulta_media_min: float | None
    total_clinica_media_min: float | None
    retraso_media_min: float | None
    descartados: int


@dataclass(frozen=True, slots=True)
class KpiMedicoDTO:
    medico_id: int
    medico_nombre: str
    total_citas: int
    espera_media_min: float | None
    consulta_media_min: float | None
    retraso_media_min: float | None


@dataclass(frozen=True, slots=True)
class ResultadoMetricasOperativasDTO:
    desde: str
    hasta: str
    por_dia: tuple[KpiDiaDTO, ...]
    por_medico: tuple[KpiMedicoDTO, ...]


class MetricasOperativasGateway(Protocol):
    def kpis_por_dia(self, desde: date, hasta: date) -> list[KpiDiaRow]:
        ...

    def kpis_por_medico(self, desde: date, hasta: date) -> list[KpiMedicoRow]:
        ...


class ObtenerMetricasOperativas:
    def __init__(self, gateway: MetricasOperativasGateway, max_dias_rango: int = 90) -> None:
        self._gateway = gateway
        self._max_dias_rango = max_dias_rango

    def execute(self, desde: date, hasta: date) -> ResultadoMetricasOperativasDTO:
        self._validar_rango(desde, hasta)
        filas_dia = self._gateway.kpis_por_dia(desde, hasta)
        filas_medico = self._gateway.kpis_por_medico(desde, hasta)
        por_dia = tuple(self._map_dia(fila) for fila in filas_dia)
        por_medico = tuple(self._map_medico(fila) for fila in filas_medico)
        LOGGER.info(
            "metricas_operativas_ok",
            extra={
                "action": "metricas_operativas_ok",
                "desde": desde.isoformat(),
                "hasta": hasta.isoformat(),
                "total_dias": len(por_dia),
                "total_medicos": len(por_medico),
            },
        )
        return ResultadoMetricasOperativasDTO(
            desde=desde.isoformat(),
            hasta=hasta.isoformat(),
            por_dia=por_dia,
            por_medico=por_medico,
        )

    def _validar_rango(self, desde: date, hasta: date) -> None:
        if hasta < desde:
            raise ValidationError("Rango de fechas inválido para métricas operativas.")
        dias_inclusivos = (hasta - desde).days + 1
        if dias_inclusivos > self._max_dias_rango:
            raise ValidationError("El rango máximo para métricas operativas es de 90 días.")

    @staticmethod
    def _map_dia(fila: KpiDiaRow) -> KpiDiaDTO:
        return KpiDiaDTO(
            fecha=fila.fecha,
            total_citas=fila.total_citas,
            espera_media_min=_round_nullable(fila.espera_media_min),
            consulta_media_min=_round_nullable(fila.consulta_media_min),
            total_clinica_media_min=_round_nullable(fila.total_clinica_media_min),
            retraso_media_min=_round_nullable(fila.retraso_media_min),
            descartados=fila.descartados,
        )

    @staticmethod
    def _map_medico(fila: KpiMedicoRow) -> KpiMedicoDTO:
        return KpiMedicoDTO(
            medico_id=fila.medico_id,
            medico_nombre=fila.medico_nombre,
            total_citas=fila.total_citas,
            espera_media_min=_round_nullable(fila.espera_media_min),
            consulta_media_min=_round_nullable(fila.consulta_media_min),
            retraso_media_min=_round_nullable(fila.retraso_media_min),
        )


def _round_nullable(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)
