from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from clinicdesk.app.application.prediccion_ausencias.dtos import CitaParaPrediccionDTO
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)
TOP_CITAS_VIGILAR_LIMITE = 10
NIVEL_ALTO = "ALTO"


@dataclass(frozen=True, slots=True)
class EstadoSaludDashboardDTO:
    estado: str
    label_i18n_key: str


@dataclass(frozen=True, slots=True)
class EstadosPrediccionDashboardDTO:
    salud_ausencias: EstadoSaludDashboardDTO
    salud_duracion: EstadoSaludDashboardDTO
    salud_espera: EstadoSaludDashboardDTO


@dataclass(frozen=True, slots=True)
class CitaVigilarDTO:
    cita_id: int
    hora: str
    paciente: str
    medico: str
    no_show_alto: bool
    duracion_alta: bool
    espera_alta: bool


@dataclass(frozen=True, slots=True)
class CitaGestionHoyDTO:
    cita_id: int
    hora: str
    paciente_nombre: str
    medico_nombre: str
    paciente_id: int
    medico_id: int
    antelacion_dias: int


class PrediccionAusenciasPort(Protocol):
    def obtener_salud(self) -> str:
        ...

    def obtener_riesgo(self, citas: tuple[CitaParaPrediccionDTO, ...]) -> dict[int, str]:
        ...


class PrediccionOperativaPort(Protocol):
    def obtener_salud_duracion(self) -> str:
        ...

    def obtener_salud_espera(self) -> str:
        ...

    def obtener_estimaciones_agenda(self) -> tuple[dict[int, str], dict[int, str]]:
        ...


class ListarCitasHoyGestionPort(Protocol):
    def listar_citas_hoy_gestion(self, limite: int) -> tuple[CitaGestionHoyDTO, ...]:
        ...


def resolver_estados_prediccion(
    prediccion_ausencias: PrediccionAusenciasPort,
    prediccion_operativa: PrediccionOperativaPort,
) -> EstadosPrediccionDashboardDTO:
    return EstadosPrediccionDashboardDTO(
        salud_ausencias=_resolver_estado_seguro(prediccion_ausencias.obtener_salud, "ausencias"),
        salud_duracion=_resolver_estado_seguro(prediccion_operativa.obtener_salud_duracion, "duracion"),
        salud_espera=_resolver_estado_seguro(prediccion_operativa.obtener_salud_espera, "espera"),
    )


def resolver_citas_a_vigilar(
    citas_hoy_queries: ListarCitasHoyGestionPort,
    prediccion_ausencias: PrediccionAusenciasPort,
    prediccion_operativa: PrediccionOperativaPort,
) -> tuple[CitaVigilarDTO, ...]:
    citas_hoy = citas_hoy_queries.listar_citas_hoy_gestion(TOP_CITAS_VIGILAR_LIMITE * 4)
    if not citas_hoy:
        return tuple()
    riesgos = _obtener_riesgo_batch(prediccion_ausencias, citas_hoy)
    duraciones, esperas = _obtener_estimaciones_batch(prediccion_operativa)
    return _construir_top_vigilancia(citas_hoy, riesgos, duraciones, esperas)


def _resolver_estado_seguro(obtener_estado: object, contexto: str) -> EstadoSaludDashboardDTO:
    try:
        estado = str(obtener_estado() or "").upper()
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("dashboard_gestion_salud_no_disponible", extra={"contexto": contexto, "error": str(exc)})
        estado = "NO_DISPONIBLE"
    if estado not in {"VERDE", "AMARILLO", "ROJO"}:
        estado = "NO_DISPONIBLE"
    return EstadoSaludDashboardDTO(estado=estado, label_i18n_key=f"dashboard_gestion.salud.label.{estado.lower()}")


def _obtener_riesgo_batch(
    prediccion_ausencias: PrediccionAusenciasPort,
    citas_hoy: tuple[CitaGestionHoyDTO, ...],
) -> dict[int, str]:
    entradas = tuple(
        CitaParaPrediccionDTO(
            id=cita.cita_id,
            fecha="",
            hora=cita.hora,
            paciente_id=cita.paciente_id,
            medico_id=cita.medico_id,
            antelacion_dias=max(0, cita.antelacion_dias),
        )
        for cita in citas_hoy
    )
    try:
        return prediccion_ausencias.obtener_riesgo(entradas)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("dashboard_gestion_riesgo_no_disponible", extra={"error": str(exc)})
        return {}


def _obtener_estimaciones_batch(prediccion_operativa: PrediccionOperativaPort) -> tuple[dict[int, str], dict[int, str]]:
    try:
        return prediccion_operativa.obtener_estimaciones_agenda()
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("dashboard_gestion_estimaciones_no_disponibles", extra={"error": str(exc)})
        return {}, {}


def _construir_top_vigilancia(
    citas_hoy: tuple[CitaGestionHoyDTO, ...],
    riesgos: dict[int, str],
    duraciones: dict[int, str],
    esperas: dict[int, str],
) -> tuple[CitaVigilarDTO, ...]:
    con_score: list[tuple[int, CitaVigilarDTO]] = []
    for cita in citas_hoy:
        dto = CitaVigilarDTO(
            cita_id=cita.cita_id,
            hora=cita.hora,
            paciente=cita.paciente_nombre,
            medico=cita.medico_nombre,
            no_show_alto=riesgos.get(cita.cita_id) == NIVEL_ALTO,
            duracion_alta=duraciones.get(cita.cita_id) == NIVEL_ALTO,
            espera_alta=esperas.get(cita.cita_id) == NIVEL_ALTO,
        )
        score = int(dto.no_show_alto) + int(dto.duracion_alta) + int(dto.espera_alta)
        if score > 0:
            con_score.append((score, dto))
    con_score.sort(key=lambda item: (-item[0], item[1].hora, item[1].cita_id))
    return tuple(dto for _, dto in con_score[:TOP_CITAS_VIGILAR_LIMITE])
