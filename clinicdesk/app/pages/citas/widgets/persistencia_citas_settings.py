from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.application.citas import FiltrosCitasDTO, obtener_columnas_default_citas, sanear_columnas_citas


_SETTINGS_PREFIJO = "citas"
_SETTINGS_FILTROS = f"{_SETTINGS_PREFIJO}/filtros"
_SETTINGS_COLUMNAS = f"{_SETTINGS_PREFIJO}/columnas"


@dataclass(frozen=True, slots=True)
class EstadoPersistidoFiltrosCitas:
    preset: str
    desde_iso: str | None
    hasta_iso: str | None
    texto: str | None
    estado: str | None
    medico_id: int | None
    sala_id: int | None
    paciente_id: int | None


def serializar_filtros_citas(filtros: FiltrosCitasDTO) -> EstadoPersistidoFiltrosCitas:
    return EstadoPersistidoFiltrosCitas(
        preset=filtros.rango_preset,
        desde_iso=filtros.desde.isoformat() if filtros.desde else None,
        hasta_iso=filtros.hasta.isoformat() if filtros.hasta else None,
        texto=filtros.texto_busqueda,
        estado=filtros.estado_cita,
        medico_id=filtros.medico_id,
        sala_id=filtros.sala_id,
        paciente_id=filtros.paciente_id,
    )


def deserializar_filtros_citas(data: EstadoPersistidoFiltrosCitas) -> FiltrosCitasDTO:
    return FiltrosCitasDTO(
        rango_preset=(data.preset or "HOY").upper(),
        desde=_parse_fecha_iso(data.desde_iso),
        hasta=_parse_fecha_iso(data.hasta_iso),
        texto_busqueda=(data.texto or "").strip() or None,
        estado_cita=(data.estado or "").strip() or None,
        medico_id=_parse_id(data.medico_id),
        sala_id=_parse_id(data.sala_id),
        paciente_id=_parse_id(data.paciente_id),
    )


def claves_filtros_citas() -> dict[str, str]:
    return {
        "preset": f"{_SETTINGS_FILTROS}/preset",
        "desde": f"{_SETTINGS_FILTROS}/desde",
        "hasta": f"{_SETTINGS_FILTROS}/hasta",
        "texto": f"{_SETTINGS_FILTROS}/texto",
        "estado": f"{_SETTINGS_FILTROS}/estado",
        "medico_id": f"{_SETTINGS_FILTROS}/medico_id",
        "sala_id": f"{_SETTINGS_FILTROS}/sala_id",
        "paciente_id": f"{_SETTINGS_FILTROS}/paciente_id",
    }


def serializar_columnas_citas(columnas: tuple[str, ...]) -> str:
    return ",".join(columnas)


def deserializar_columnas_citas(valor: str | None) -> tuple[str, ...]:
    if not valor:
        return tuple(obtener_columnas_default_citas())
    columnas = tuple(item.strip() for item in valor.split(",") if item.strip())
    saneadas, _ = sanear_columnas_citas(columnas)
    return saneadas


def clave_columnas_citas() -> str:
    return f"{_SETTINGS_COLUMNAS}/seleccion"


def estado_restauracion_columnas(valor: str | None) -> bool:
    columnas = tuple(item.strip() for item in (valor or "").split(",") if item.strip())
    _, restauradas = sanear_columnas_citas(columnas)
    return restauradas


def _parse_fecha_iso(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


def _parse_id(valor: int | None) -> int | None:
    return valor if isinstance(valor, int) and valor > 0 else None
