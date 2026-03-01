from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.pages.citas.estado_cita_presentacion import etiqueta_estado_cita
from clinicdesk.app.queries.citas_queries import CitaListadoRow, CitaRow


@dataclass(frozen=True, slots=True)
class AtributoCita:
    clave: str
    clave_i18n: str
    visible_por_defecto: bool
    tooltip_por_defecto: bool


ATRIBUTOS_CITA: tuple[AtributoCita, ...] = (
    AtributoCita("fecha", "citas.atributo.fecha", True, True),
    AtributoCita("hora_inicio", "citas.atributo.hora_inicio", True, True),
    AtributoCita("hora_fin", "citas.atributo.hora_fin", True, False),
    AtributoCita("paciente", "citas.atributo.paciente", True, True),
    AtributoCita("medico", "citas.atributo.medico", True, True),
    AtributoCita("sala", "citas.atributo.sala", True, True),
    AtributoCita("estado", "citas.atributo.estado", True, True),
    AtributoCita("riesgo", "citas.riesgo.columna", False, True),
    AtributoCita("recordatorio", "citas.atributo.recordatorio", False, True),
    AtributoCita("incidencias", "citas.atributo.incidencias", True, False),
    AtributoCita("notas_len", "citas.atributo.notas_len", False, False),
)


def claves_visibles_por_defecto() -> list[str]:
    return [atributo.clave for atributo in ATRIBUTOS_CITA if atributo.visible_por_defecto]


def claves_tooltip_por_defecto() -> list[str]:
    return [atributo.clave for atributo in ATRIBUTOS_CITA if atributo.tooltip_por_defecto]


def valor_lista_por_clave(cita: CitaListadoRow, clave: str, *, i18n, riesgo: str) -> str:
    if clave == "fecha":
        return cita.fecha
    if clave == "hora_inicio":
        return cita.hora_inicio
    if clave == "hora_fin":
        return cita.hora_fin
    if clave == "paciente":
        return cita.paciente
    if clave == "medico":
        return cita.medico
    if clave == "sala":
        return cita.sala
    if clave == "estado":
        return etiqueta_estado_cita(cita.estado)
    if clave == "riesgo":
        return riesgo
    if clave == "recordatorio":
        return i18n.t("comun.no")
    if clave == "incidencias":
        return i18n.t("comun.si") if cita.tiene_incidencias else i18n.t("comun.no")
    if clave == "notas_len":
        return str(cita.notas_len)
    return ""


def valor_calendario_por_clave(cita: CitaRow, clave: str, *, i18n, riesgo: str) -> str:
    if clave == "fecha":
        return cita.inicio[:10]
    if clave == "hora_inicio":
        return cita.inicio[11:16]
    if clave == "hora_fin":
        return cita.fin[11:16]
    if clave == "paciente":
        return cita.paciente_nombre
    if clave == "medico":
        return cita.medico_nombre
    if clave == "sala":
        return cita.sala_nombre
    if clave == "estado":
        return etiqueta_estado_cita(cita.estado)
    if clave == "riesgo":
        return riesgo
    if clave == "recordatorio":
        return i18n.t("comun.no")
    if clave == "incidencias":
        return ""
    if clave == "notas_len":
        return str(len(cita.motivo or ""))
    return ""
