from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable

FormateadorAtributo = Callable[[dict[str, object]], str]


class SensibilidadAtributo(str, Enum):
    PUBLICO = "PUBLICO"
    PERSONAL = "PERSONAL"
    SENSIBLE = "SENSIBLE"


@dataclass(frozen=True, slots=True)
class AtributoHistorial:
    clave: str
    i18n_key_cabecera: str
    i18n_key_tooltip: str | None
    formateador: FormateadorAtributo
    visible_por_defecto: bool
    sensibilidad: SensibilidadAtributo


def _fmt_texto(clave: str, valor_none: str = "") -> FormateadorAtributo:
    def _formatear(fila: dict[str, object]) -> str:
        valor = fila.get(clave)
        if valor is None:
            return valor_none
        return str(valor)

    return _formatear


def _fmt_iso_datetime(clave: str, formato: str) -> FormateadorAtributo:
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


def _fmt_bool(clave: str, true_txt: str = "Sí", false_txt: str = "No") -> FormateadorAtributo:
    def _formatear(fila: dict[str, object]) -> str:
        return true_txt if bool(fila.get(clave)) else false_txt

    return _formatear


def _fmt_len_texto(clave: str) -> FormateadorAtributo:
    def _formatear(fila: dict[str, object]) -> str:
        valor = fila.get(clave)
        return str(len(str(valor).strip())) if valor else "0"

    return _formatear


ATRIBUTOS_HISTORIAL_CITAS: tuple[AtributoHistorial, ...] = (
    AtributoHistorial(
        "cita_id", "historial.citas.col.id", None, _fmt_texto("cita_id"), False, SensibilidadAtributo.PUBLICO
    ),
    AtributoHistorial(
        "fecha",
        "historial.citas.col.fecha",
        "historial.citas.tip.fecha",
        _fmt_iso_datetime("inicio", "%Y-%m-%d"),
        True,
        SensibilidadAtributo.PUBLICO,
    ),
    AtributoHistorial(
        "hora_inicio",
        "historial.citas.col.hora_inicio",
        "historial.citas.tip.hora_inicio",
        _fmt_iso_datetime("inicio", "%H:%M"),
        True,
        SensibilidadAtributo.PUBLICO,
    ),
    AtributoHistorial(
        "estado",
        "historial.citas.col.estado",
        "historial.citas.tip.estado",
        _fmt_texto("estado"),
        True,
        SensibilidadAtributo.PUBLICO,
    ),
    AtributoHistorial(
        "medico",
        "historial.citas.col.medico",
        "historial.citas.tip.medico",
        _fmt_texto("medico"),
        True,
        SensibilidadAtributo.PERSONAL,
    ),
    AtributoHistorial(
        "tiene_incidencias",
        "historial.citas.col.incidencias",
        "historial.citas.tip.incidencias",
        _fmt_bool("tiene_incidencias"),
        True,
        SensibilidadAtributo.PUBLICO,
    ),
    AtributoHistorial(
        "informe_len",
        "historial.citas.col.informe_len",
        "historial.citas.tip.informe_len",
        _fmt_len_texto("resumen"),
        False,
        SensibilidadAtributo.SENSIBLE,
    ),
)

ATRIBUTOS_HISTORIAL_RECETAS: tuple[AtributoHistorial, ...] = (
    AtributoHistorial(
        "receta_id", "historial.recetas.col.id", None, _fmt_texto("receta_id"), False, SensibilidadAtributo.PUBLICO
    ),
    AtributoHistorial(
        "fecha",
        "historial.recetas.col.fecha",
        "historial.recetas.tip.fecha",
        _fmt_iso_datetime("receta_fecha", "%Y-%m-%d"),
        True,
        SensibilidadAtributo.PUBLICO,
    ),
    AtributoHistorial(
        "estado",
        "historial.recetas.col.estado",
        "historial.recetas.tip.estado",
        _fmt_texto("receta_estado"),
        True,
        SensibilidadAtributo.PUBLICO,
    ),
    AtributoHistorial(
        "medico",
        "historial.recetas.col.medico",
        "historial.recetas.tip.medico",
        _fmt_texto("medico_nombre"),
        True,
        SensibilidadAtributo.PERSONAL,
    ),
    AtributoHistorial(
        "num_lineas",
        "historial.recetas.col.num_lineas",
        "historial.recetas.tip.num_lineas",
        _fmt_texto("num_lineas", "0"),
        True,
        SensibilidadAtributo.PUBLICO,
    ),
    AtributoHistorial(
        "activa",
        "historial.recetas.col.activa",
        "historial.recetas.tip.activa",
        _fmt_bool("activa"),
        True,
        SensibilidadAtributo.PUBLICO,
    ),
    AtributoHistorial(
        "observaciones_len",
        "historial.recetas.col.observaciones_len",
        "historial.recetas.tip.observaciones_len",
        _fmt_len_texto("observaciones"),
        False,
        SensibilidadAtributo.SENSIBLE,
    ),
)


def obtener_columnas_default_historial_citas() -> tuple[str, ...]:
    return _obtener_columnas_default(ATRIBUTOS_HISTORIAL_CITAS)


def obtener_columnas_default_historial_recetas() -> tuple[str, ...]:
    return _obtener_columnas_default(ATRIBUTOS_HISTORIAL_RECETAS)


def _obtener_columnas_default(contrato: tuple[AtributoHistorial, ...]) -> tuple[str, ...]:
    return tuple(atributo.clave for atributo in contrato if atributo.visible_por_defecto)


def sanear_columnas_solicitadas(
    columnas: tuple[str, ...] | list[str] | None,
    contrato: tuple[AtributoHistorial, ...],
) -> tuple[tuple[str, ...], bool]:
    claves_validas = {atributo.clave for atributo in contrato}
    if not columnas:
        return _obtener_columnas_default(contrato), True
    saneadas: list[str] = []
    for clave in columnas:
        if not isinstance(clave, str) or clave not in claves_validas or clave in saneadas:
            continue
        saneadas.append(clave)
    if saneadas:
        return tuple(saneadas), tuple(saneadas) != tuple(columnas)
    return _obtener_columnas_default(contrato), True
