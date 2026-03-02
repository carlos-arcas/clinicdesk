from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Callable


FormateadorAtributo = Callable[[dict[str, object]], str]


class SensibilidadAtributo(StrEnum):
    PUBLICO = "PUBLICO"
    PERSONAL = "PERSONAL"
    SENSIBLE = "SENSIBLE"


@dataclass(frozen=True, slots=True)
class DescriptorAtributoCita:
    clave: str
    i18n_key_cabecera: str
    i18n_key_tooltip: str | None
    visible_por_defecto: bool
    sensibilidad: SensibilidadAtributo
    formateador_puro: FormateadorAtributo


def _fmt_texto(clave: str) -> FormateadorAtributo:
    def _formatear(fila: dict[str, object]) -> str:
        valor = fila.get(clave)
        return "" if valor is None else str(valor)

    return _formatear


def _fmt_datetime(clave: str, formato: str) -> FormateadorAtributo:
    def _formatear(fila: dict[str, object]) -> str:
        valor = fila.get(clave)
        if valor is None:
            return ""
        if isinstance(valor, datetime):
            return valor.strftime(formato)
        try:
            return datetime.fromisoformat(str(valor)).strftime(formato)
        except ValueError:
            return str(valor)

    return _formatear


ATRIBUTOS_CITA: tuple[DescriptorAtributoCita, ...] = (
    DescriptorAtributoCita("fecha", "citas.lista.col.fecha", "citas.lista.tooltip.fecha", True, SensibilidadAtributo.PUBLICO, _fmt_datetime("inicio", "%Y-%m-%d")),
    DescriptorAtributoCita("hora_inicio", "citas.lista.col.hora_inicio", "citas.lista.tooltip.hora_inicio", True, SensibilidadAtributo.PUBLICO, _fmt_datetime("inicio", "%H:%M")),
    DescriptorAtributoCita("hora_fin", "citas.lista.col.hora_fin", "citas.lista.tooltip.hora_fin", True, SensibilidadAtributo.PUBLICO, _fmt_datetime("fin", "%H:%M")),
    DescriptorAtributoCita("paciente", "citas.lista.col.paciente", "citas.lista.tooltip.paciente", True, SensibilidadAtributo.PERSONAL, _fmt_texto("paciente")),
    DescriptorAtributoCita("medico", "citas.lista.col.medico", "citas.lista.tooltip.medico", True, SensibilidadAtributo.PERSONAL, _fmt_texto("medico")),
    DescriptorAtributoCita("sala", "citas.lista.col.sala", "citas.lista.tooltip.sala", True, SensibilidadAtributo.PUBLICO, _fmt_texto("sala")),
    DescriptorAtributoCita("estado", "citas.lista.col.estado", "citas.lista.tooltip.estado", True, SensibilidadAtributo.PUBLICO, _fmt_texto("estado")),
    DescriptorAtributoCita("riesgo_ausencia", "citas.lista.col.riesgo", "citas.lista.tooltip.riesgo", False, SensibilidadAtributo.PERSONAL, _fmt_texto("riesgo_ausencia")),
    DescriptorAtributoCita("recordatorio_estado", "citas.lista.col.recordatorio", "citas.lista.tooltip.recordatorio", False, SensibilidadAtributo.PUBLICO, _fmt_texto("recordatorio_estado")),
    DescriptorAtributoCita("notas_len", "citas.lista.col.notas_len", "citas.lista.tooltip.notas_len", True, SensibilidadAtributo.SENSIBLE, _fmt_texto("notas_len")),
    DescriptorAtributoCita("incidencias", "citas.lista.col.incidencias", "citas.lista.tooltip.incidencias", True, SensibilidadAtributo.PUBLICO, _fmt_texto("tiene_incidencias")),
    DescriptorAtributoCita("cita_id", "citas.lista.col.cita_id", None, False, SensibilidadAtributo.PUBLICO, _fmt_texto("cita_id")),
)


def obtener_columnas_default_citas() -> tuple[str, ...]:
    return tuple(item.clave for item in ATRIBUTOS_CITA if item.visible_por_defecto)


def sanear_columnas_citas(columnas: tuple[str, ...] | list[str] | None) -> tuple[tuple[str, ...], bool]:
    claves_validas = {atributo.clave for atributo in ATRIBUTOS_CITA}
    ordenadas: list[str] = []
    for columna in columnas or ():
        if columna in claves_validas and columna not in ordenadas:
            ordenadas.append(columna)
    restauradas = not ordenadas
    if restauradas:
        ordenadas.extend(obtener_columnas_default_citas())
    if "cita_id" not in ordenadas:
        ordenadas.append("cita_id")
    return tuple(ordenadas), restauradas


def formatear_valor_atributo_cita(clave: str, fila: dict[str, object]) -> str:
    descriptor = next((item for item in ATRIBUTOS_CITA if item.clave == clave), None)
    if descriptor is None:
        raise KeyError(f"Atributo de cita no soportado: {clave}")
    return descriptor.formateador_puro(fila)
