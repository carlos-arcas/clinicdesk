from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.application.prediccion_ausencias.dtos import CitaParaPrediccionDTO
from clinicdesk.app.application.prediccion_ausencias.riesgo_agenda import RIESGO_NO_DISPONIBLE
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.queries.citas_queries import CitaListadoRow, CitaRow

SETTINGS_KEY_RIESGO_AGENDA = "prediccion_ausencias/mostrar_riesgo_agenda"


@dataclass(frozen=True, slots=True)
class ResultadoRiesgoTexto:
    texto: str
    no_disponible: bool


def construir_dtos_desde_listado(rows: list[CitaListadoRow], hoy: datetime) -> list[CitaParaPrediccionDTO]:
    return [
        CitaParaPrediccionDTO(
            id=row.id,
            fecha=row.fecha,
            hora=row.hora_inicio,
            paciente_id=row.paciente_id,
            medico_id=row.medico_id,
            antelacion_dias=_calcular_antelacion(row.fecha, row.hora_inicio, hoy),
        )
        for row in rows
    ]


def construir_dtos_desde_calendario(rows: list[CitaRow], hoy: datetime) -> list[CitaParaPrediccionDTO]:
    return [
        CitaParaPrediccionDTO(
            id=row.id,
            fecha=row.inicio[:10],
            hora=row.inicio[11:19],
            paciente_id=row.paciente_id,
            medico_id=row.medico_id,
            antelacion_dias=_calcular_antelacion(row.inicio[:10], row.inicio[11:19], hoy),
        )
        for row in rows
    ]


def resolver_texto_riesgo(riesgo: str, i18n: I18nManager) -> ResultadoRiesgoTexto:
    if riesgo == RIESGO_NO_DISPONIBLE:
        return ResultadoRiesgoTexto(
            texto=i18n.t("citas.riesgo.no_disponible"),
            no_disponible=True,
        )
    return ResultadoRiesgoTexto(
        texto=i18n.t(f"citas.riesgo.valor.{riesgo.lower()}"),
        no_disponible=False,
    )


def tooltip_riesgo(riesgo: str, i18n: I18nManager) -> str:
    valor = resolver_texto_riesgo(riesgo, i18n).texto
    return i18n.t("citas.riesgo.tooltip").format(nivel=valor)


def _calcular_antelacion(fecha: str, hora: str, hoy: datetime) -> int:
    inicio = datetime.fromisoformat(f"{fecha} {hora}")
    return max(0, (inicio.date() - hoy.date()).days)
