from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable


FormateadorAtributo = Callable[[dict[str, object]], str]


@dataclass(frozen=True, slots=True)
class AtributoCita:
    clave: str
    i18n_key_cabecera: str
    i18n_key_tooltip: str
    formateador_presentacion: FormateadorAtributo
    visible_por_defecto: bool = True


def _fmt_texto(clave: str) -> FormateadorAtributo:
    def _formatear(fila: dict[str, object]) -> str:
        valor = fila.get(clave)
        if valor is None:
            return ""
        return str(valor)

    return _formatear


def _fmt_datetime(clave: str, formato: str) -> FormateadorAtributo:
    def _formatear(fila: dict[str, object]) -> str:
        valor = fila.get(clave)
        if valor is None:
            return ""
        if isinstance(valor, datetime):
            return valor.strftime(formato)
        texto = str(valor)
        try:
            return datetime.fromisoformat(texto).strftime(formato)
        except ValueError:
            return texto

    return _formatear


ATRIBUTOS_CITA: tuple[AtributoCita, ...] = (
    AtributoCita("fecha", "citas.lista.col.fecha", "citas.lista.tooltip.fecha", _fmt_datetime("inicio", "%Y-%m-%d")),
    AtributoCita(
        "hora_inicio",
        "citas.lista.col.hora_inicio",
        "citas.lista.tooltip.hora_inicio",
        _fmt_datetime("inicio", "%H:%M"),
    ),
    AtributoCita("hora_fin", "citas.lista.col.hora_fin", "citas.lista.tooltip.hora_fin", _fmt_datetime("fin", "%H:%M")),
    AtributoCita("paciente", "citas.lista.col.paciente", "citas.lista.tooltip.paciente", _fmt_texto("paciente")),
    AtributoCita("medico", "citas.lista.col.medico", "citas.lista.tooltip.medico", _fmt_texto("medico")),
    AtributoCita("sala", "citas.lista.col.sala", "citas.lista.tooltip.sala", _fmt_texto("sala")),
    AtributoCita("estado", "citas.lista.col.estado", "citas.lista.tooltip.estado", _fmt_texto("estado")),
    AtributoCita("riesgo", "citas.lista.col.riesgo", "citas.lista.tooltip.riesgo", _fmt_texto("riesgo"), False),
    AtributoCita(
        "recordatorio",
        "citas.lista.col.recordatorio",
        "citas.lista.tooltip.recordatorio",
        _fmt_texto("recordatorio"),
        False,
    ),
    AtributoCita("notas_len", "citas.lista.col.notas_len", "citas.lista.tooltip.notas_len", _fmt_texto("notas_len")),
    AtributoCita(
        "incidencias",
        "citas.lista.col.incidencias",
        "citas.lista.tooltip.incidencias",
        _fmt_texto("tiene_incidencias"),
    ),
)


def obtener_atributos_cita_visibles_por_defecto() -> tuple[AtributoCita, ...]:
    return tuple(atributo for atributo in ATRIBUTOS_CITA if atributo.visible_por_defecto)


def formatear_valor_atributo_cita(clave: str, fila: dict[str, object]) -> str:
    descriptor = next((item for item in ATRIBUTOS_CITA if item.clave == clave), None)
    if descriptor is None:
        raise KeyError(f"Atributo de cita no soportado: {clave}")
    return descriptor.formateador_presentacion(fila)
