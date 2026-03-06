from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from clinicdesk.app.application.citas.navigation_intent import CitasNavigationIntentDTO
from clinicdesk.app.application.usecases.centro_salud_operativa import AlertaCentroSaludDTO, FiltrosCentroSaludDTO

TipoDrilldown = Literal["KPI", "ALERTA"]


@dataclass(frozen=True, slots=True)
class DrilldownAccionDTO:
    clave: str
    tipo: TipoDrilldown
    descripcion_i18n_key: str
    accion_i18n_key: str
    destino: str | None
    intent_citas: CitasNavigationIntentDTO | None = None
    motivo_no_disponible_i18n_key: str | None = None

    @property
    def disponible(self) -> bool:
        return self.destino is not None


def construir_acciones_kpi(
    filtros: FiltrosCentroSaludDTO, *, riesgo_disponible: bool
) -> tuple[DrilldownAccionDTO, ...]:
    return (
        _accion_kpi_estado("pendientes", filtros, "PROGRAMADA"),
        _accion_kpi_estado("canceladas_no_show", filtros, "CANCELADA"),
        _accion_kpi_estado("tasa_no_asistencia", filtros, "NO_PRESENTADO"),
        _accion_kpi_riesgo(filtros, riesgo_disponible),
    )


def construir_accion_alerta(alerta: AlertaCentroSaludDTO, filtros: FiltrosCentroSaludDTO) -> DrilldownAccionDTO:
    base = "dashboard_gestion.operativa.drilldown.alerta"
    if alerta.i18n_key == "dashboard_gestion.operativa.alerta.riesgo_alto":
        return DrilldownAccionDTO(
            clave="riesgo_alto",
            tipo="ALERTA",
            descripcion_i18n_key=alerta.i18n_key,
            accion_i18n_key=f"{base}.riesgo_alto.accion",
            destino="citas",
            intent_citas=_intent_citas_periodo(filtros, estado_cita="NO_PRESENTADO", incluir_riesgo=True),
        )
    if alerta.i18n_key == "dashboard_gestion.operativa.alerta.pacientes_riesgo":
        return DrilldownAccionDTO(
            clave="pacientes_riesgo",
            tipo="ALERTA",
            descripcion_i18n_key=alerta.i18n_key,
            accion_i18n_key=f"{base}.pacientes_riesgo.accion",
            destino=None,
            motivo_no_disponible_i18n_key="dashboard_gestion.operativa.drilldown.sin_destino.paciente",
        )
    if alerta.i18n_key == "dashboard_gestion.operativa.alerta.cuellos":
        return DrilldownAccionDTO(
            clave="cuellos",
            tipo="ALERTA",
            descripcion_i18n_key=alerta.i18n_key,
            accion_i18n_key=f"{base}.cuellos.accion",
            destino="confirmaciones",
        )
    return DrilldownAccionDTO(
        clave="sin_alertas",
        tipo="ALERTA",
        descripcion_i18n_key=alerta.i18n_key,
        accion_i18n_key=f"{base}.sin_alertas.accion",
        destino="citas",
        intent_citas=_intent_citas_periodo(filtros),
    )


def _accion_kpi_estado(clave: str, filtros: FiltrosCentroSaludDTO, estado_cita: str) -> DrilldownAccionDTO:
    return DrilldownAccionDTO(
        clave=clave,
        tipo="KPI",
        descripcion_i18n_key=f"dashboard_gestion.operativa.drilldown.kpi.{clave}",
        accion_i18n_key=f"dashboard_gestion.operativa.drilldown.kpi.{clave}.accion",
        destino="citas",
        intent_citas=_intent_citas_periodo(filtros, estado_cita=estado_cita),
    )


def _accion_kpi_riesgo(filtros: FiltrosCentroSaludDTO, riesgo_disponible: bool) -> DrilldownAccionDTO:
    if not riesgo_disponible:
        return DrilldownAccionDTO(
            clave="riesgo",
            tipo="KPI",
            descripcion_i18n_key="dashboard_gestion.operativa.drilldown.kpi.riesgo",
            accion_i18n_key="dashboard_gestion.operativa.drilldown.kpi.riesgo.accion",
            destino=None,
            motivo_no_disponible_i18n_key="dashboard_gestion.operativa.drilldown.sin_destino.riesgo",
        )
    return DrilldownAccionDTO(
        clave="riesgo",
        tipo="KPI",
        descripcion_i18n_key="dashboard_gestion.operativa.drilldown.kpi.riesgo",
        accion_i18n_key="dashboard_gestion.operativa.drilldown.kpi.riesgo.accion",
        destino="citas",
        intent_citas=_intent_citas_periodo(filtros, incluir_riesgo=True),
    )


def _intent_citas_periodo(
    filtros: FiltrosCentroSaludDTO,
    *,
    estado_cita: str | None = None,
    incluir_riesgo: bool = False,
) -> CitasNavigationIntentDTO:
    return CitasNavigationIntentDTO(
        preset_rango="PERSONALIZADO",
        rango_desde=datetime(filtros.desde.year, filtros.desde.month, filtros.desde.day, 0, 0, 0),
        rango_hasta=datetime(filtros.hasta.year, filtros.hasta.month, filtros.hasta.day, 23, 59, 59),
        preferir_pestana="LISTA",
        estado_cita=estado_cita,
        incluir_riesgo=incluir_riesgo,
    )
