from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Sequence

from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.domain.citas_atributos import ATRIBUTOS_CITA, claves_atributos_cita
from clinicdesk.app.domain.enums import EstadoCita

MAX_RANGO_DIAS_CITAS = 365
MAX_TEXTO_BUSQUEDA = 100


@dataclass(frozen=True, slots=True)
class ErrorValidacion:
    code: str
    i18n_key: str
    campo: str


@dataclass(frozen=True, slots=True)
class ResultadoValidacion:
    ok: bool
    errores: tuple[ErrorValidacion, ...]


@dataclass(frozen=True, slots=True)
class ResultadoColumnasCita:
    columnas: tuple[str, ...]
    restauradas: bool


def normalizar_filtros_citas(filtros: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "desde": _normalizar_fecha(filtros.get("desde")),
        "hasta": _normalizar_fecha(filtros.get("hasta")),
        "estado": _normalizar_texto_mayus(filtros.get("estado")),
        "texto_busqueda": normalize_search_text(_normalizar_str(filtros.get("texto_busqueda"))),
        "medico_id": _normalizar_id(filtros.get("medico_id")),
        "sala_id": _normalizar_id(filtros.get("sala_id")),
        "paciente_id": _normalizar_id(filtros.get("paciente_id")),
    }


def validar_filtros_citas(filtros_norm: Mapping[str, Any]) -> ResultadoValidacion:
    errores: list[ErrorValidacion] = []
    desde = _parse_fecha(filtros_norm.get("desde"))
    hasta = _parse_fecha(filtros_norm.get("hasta"))

    errores.extend(_validar_rango_fechas(desde, hasta))
    errores.extend(_validar_estado(filtros_norm.get("estado")))
    errores.extend(_validar_ids(filtros_norm))
    errores.extend(_validar_texto(filtros_norm.get("texto_busqueda")))

    return ResultadoValidacion(ok=not errores, errores=tuple(errores))


def resolver_columnas_cita(columnas: Sequence[str] | None) -> ResultadoColumnasCita:
    defaults = claves_atributos_cita()
    if not columnas:
        return ResultadoColumnasCita(columnas=defaults, restauradas=False)

    permitidas = {atributo.clave for atributo in ATRIBUTOS_CITA}
    seleccionadas = tuple(col for col in columnas if col in permitidas)
    if len(seleccionadas) != len(columnas) or not seleccionadas:
        return ResultadoColumnasCita(columnas=defaults, restauradas=True)
    return ResultadoColumnasCita(columnas=seleccionadas, restauradas=False)


def _validar_rango_fechas(desde: date | None, hasta: date | None) -> list[ErrorValidacion]:
    if desde is None or hasta is None:
        return [ErrorValidacion("fechas_requeridas", "citas.validacion.fechas_invertidas", "rango")]
    if desde > hasta:
        return [ErrorValidacion("fechas_invertidas", "citas.validacion.fechas_invertidas", "rango")]
    if (hasta - desde).days > MAX_RANGO_DIAS_CITAS:
        return [
            ErrorValidacion(
                "rango_demasiado_grande",
                "citas.validacion.rango_demasiado_grande",
                "rango",
            )
        ]
    return []


def _validar_estado(estado: Any) -> list[ErrorValidacion]:
    if not estado:
        return []
    permitidos = {item.value for item in EstadoCita} | {"TODOS"}
    if estado in permitidos:
        return []
    return [ErrorValidacion("estado_invalido", "citas.validacion.estado_invalido", "estado")]


def _validar_ids(filtros: Mapping[str, Any]) -> list[ErrorValidacion]:
    errores: list[ErrorValidacion] = []
    for campo in ("medico_id", "sala_id", "paciente_id"):
        valor = filtros.get(campo)
        if valor is None:
            continue
        if isinstance(valor, int) and valor > 0:
            continue
        errores.append(ErrorValidacion("id_invalido", "citas.validacion.id_invalido", campo))
    return errores


def _validar_texto(texto: Any) -> list[ErrorValidacion]:
    if not texto:
        return []
    if len(texto) <= MAX_TEXTO_BUSQUEDA:
        return []
    return [
        ErrorValidacion(
            "texto_demasiado_largo",
            "citas.validacion.texto_demasiado_largo",
            "texto_busqueda",
        )
    ]


def _normalizar_fecha(valor: Any) -> str | None:
    if isinstance(valor, date):
        return valor.isoformat()
    texto = _normalizar_str(valor)
    if not texto:
        return None
    return texto[:10]


def _normalizar_str(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _normalizar_texto_mayus(valor: Any) -> str | None:
    texto = _normalizar_str(valor)
    return texto.upper() if texto else None


def _normalizar_id(valor: Any) -> int | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, bool):
        return int(valor)
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return -1


def _parse_fecha(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None
