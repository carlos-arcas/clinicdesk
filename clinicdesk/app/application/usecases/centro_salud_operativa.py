from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class FiltrosCentroSaludDTO:
    desde: date
    hasta: date
    medico_id: int | None = None
    sala_id: int | None = None
    estado: str | None = None


@dataclass(frozen=True, slots=True)
class KpiCentroSaludDTO:
    total_citas: int
    completadas: int
    pendientes: int
    canceladas_no_show: int
    no_show: int
    tasa_no_asistencia_pct: float
    riesgo_medio_pct: float | None


@dataclass(frozen=True, slots=True)
class AlertaCentroSaludDTO:
    severidad: str
    i18n_key: str
    total: int


@dataclass(frozen=True, slots=True)
class CentroSaludOperativaDTO:
    kpis: KpiCentroSaludDTO
    alertas: tuple[AlertaCentroSaludDTO, ...]


class CentroSaludOperativaQueriesPort(Protocol):
    def obtener_resumen_centro_salud(
        self,
        desde: date,
        hasta: date,
        medico_id: int | None,
        sala_id: int | None,
        estado: str | None,
    ): ...

    def contar_pacientes_riesgo_operativo(self, desde: date, hasta: date) -> int: ...

    def contar_cuellos_botella(self, desde: date, hasta: date, medico_id: int | None, sala_id: int | None) -> int: ...


class ObtenerCentroSaludOperativa:
    def __init__(self, queries: CentroSaludOperativaQueriesPort) -> None:
        self._queries = queries

    def execute(self, filtros: FiltrosCentroSaludDTO) -> CentroSaludOperativaDTO:
        resumen = self._queries.obtener_resumen_centro_salud(
            filtros.desde,
            filtros.hasta,
            filtros.medico_id,
            filtros.sala_id,
            filtros.estado,
        )
        tasa = _pct(resumen.total_no_presentadas, resumen.total_citas)
        kpis = KpiCentroSaludDTO(
            total_citas=resumen.total_citas,
            completadas=resumen.total_completadas,
            pendientes=resumen.total_pendientes,
            canceladas_no_show=resumen.total_canceladas,
            no_show=resumen.total_no_presentadas,
            tasa_no_asistencia_pct=tasa,
            riesgo_medio_pct=round(resumen.riesgo_medio_pct, 2) if resumen.riesgo_medio_pct is not None else None,
        )
        return CentroSaludOperativaDTO(kpis=kpis, alertas=self._derivar_alertas(filtros, resumen.total_riesgo_alto))

    def _derivar_alertas(self, filtros: FiltrosCentroSaludDTO, total_riesgo_alto: int) -> tuple[AlertaCentroSaludDTO, ...]:
        alertas: list[AlertaCentroSaludDTO] = []
        if total_riesgo_alto > 0:
            alertas.append(AlertaCentroSaludDTO(severidad="ALTA", i18n_key="dashboard_gestion.operativa.alerta.riesgo_alto", total=total_riesgo_alto))
        pacientes = self._queries.contar_pacientes_riesgo_operativo(filtros.desde, filtros.hasta)
        if pacientes > 0:
            alertas.append(AlertaCentroSaludDTO(severidad="MEDIA", i18n_key="dashboard_gestion.operativa.alerta.pacientes_riesgo", total=pacientes))
        cuellos = self._queries.contar_cuellos_botella(filtros.desde, filtros.hasta, filtros.medico_id, filtros.sala_id)
        if cuellos > 0:
            alertas.append(AlertaCentroSaludDTO(severidad="MEDIA", i18n_key="dashboard_gestion.operativa.alerta.cuellos", total=cuellos))
        if not alertas:
            alertas.append(AlertaCentroSaludDTO(severidad="SUAVE", i18n_key="dashboard_gestion.operativa.alerta.sin_alertas", total=0))
        return tuple(alertas)


def _pct(parte: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((parte * 100.0) / total, 2)
