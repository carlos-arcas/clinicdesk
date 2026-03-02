from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

_PRESETS_VALIDOS = {"HOY", "30_DIAS", "12_MESES", "TODO", "PERSONALIZADO"}
_LIMITE_POR_DEFECTO = 50
_OFFSET_POR_DEFECTO = 0
_LIMITE_MAXIMO = 200


@dataclass(frozen=True, slots=True)
class FiltrosHistorialPacienteDTO:
    paciente_id: int
    rango_preset: str = "30_DIAS"
    desde: datetime | None = None
    hasta: datetime | None = None
    texto: str | None = None
    estados: tuple[str, ...] | None = None
    limite: int | None = None
    offset: int | None = None


def normalizar_filtros_historial_paciente(
    filtros: FiltrosHistorialPacienteDTO,
    ahora: datetime,
) -> FiltrosHistorialPacienteDTO:
    """Normaliza filtros de historial para todas las pestañas.

    Reglas:
    - rango_preset inválido -> "30_DIAS".
    - HOY, 30_DIAS, 12_MESES y TODO calculan automáticamente desde/hasta.
    - PERSONALIZADO conserva el rango recibido; si falta un borde usa "30_DIAS".
    - Si desde > hasta, el rango se reordena para garantizar desde <= hasta.
    - texto se recorta (trim); si queda vacío retorna None.
    - estados se normaliza a mayúsculas, sin vacíos, sin duplicados y orden estable.
    - limite por defecto = 50, offset por defecto = 0, con clamp de limite <= 200.
    """
    preset = _normalizar_preset(filtros.rango_preset)
    desde, hasta = _resolver_rango(preset, filtros.desde, filtros.hasta, ahora)
    return FiltrosHistorialPacienteDTO(
        paciente_id=_normalizar_paciente_id(filtros.paciente_id),
        rango_preset=preset,
        desde=desde,
        hasta=hasta,
        texto=_normalizar_texto(filtros.texto),
        estados=_normalizar_estados(filtros.estados),
        limite=_normalizar_limite(filtros.limite),
        offset=_normalizar_offset(filtros.offset),
    )


def _normalizar_preset(preset: str) -> str:
    valor = (preset or "").strip().upper()
    return valor if valor in _PRESETS_VALIDOS else "30_DIAS"


def _resolver_rango(
    preset: str,
    desde: datetime | None,
    hasta: datetime | None,
    ahora: datetime,
) -> tuple[datetime | None, datetime | None]:
    if preset == "TODO":
        return None, None
    if preset == "HOY":
        return _rango_hoy(ahora)
    if preset == "30_DIAS":
        return _rango_dias(ahora, dias=30)
    if preset == "12_MESES":
        return _rango_dias(ahora, dias=365)
    if desde is None or hasta is None:
        return _rango_dias(ahora, dias=30)
    return _ordenar_rango(desde, hasta)


def _rango_hoy(ahora: datetime) -> tuple[datetime, datetime]:
    inicio = datetime(ahora.year, ahora.month, ahora.day)
    fin = inicio + timedelta(hours=23, minutes=59, seconds=59)
    return inicio, fin


def _rango_dias(ahora: datetime, dias: int) -> tuple[datetime, datetime]:
    fin = datetime(ahora.year, ahora.month, ahora.day, 23, 59, 59)
    inicio = fin - timedelta(days=dias - 1, hours=23, minutes=59, seconds=59)
    return inicio, fin


def _ordenar_rango(desde: datetime, hasta: datetime) -> tuple[datetime, datetime]:
    if desde <= hasta:
        return desde, hasta
    return hasta, desde


def _normalizar_texto(texto: str | None) -> str | None:
    valor = (texto or "").strip()
    return valor or None


def _normalizar_estados(estados: tuple[str, ...] | None) -> tuple[str, ...] | None:
    if not estados:
        return None
    salida: list[str] = []
    for estado in estados:
        valor = (estado or "").strip().upper()
        if not valor or valor in salida:
            continue
        salida.append(valor)
    return tuple(salida) or None


def _normalizar_paciente_id(paciente_id: int) -> int:
    return int(paciente_id)


def _normalizar_limite(limite: int | None) -> int:
    if limite is None:
        return _LIMITE_POR_DEFECTO
    if limite <= 0:
        return _LIMITE_POR_DEFECTO
    return min(limite, _LIMITE_MAXIMO)


def _normalizar_offset(offset: int | None) -> int:
    if offset is None or offset < 0:
        return _OFFSET_POR_DEFECTO
    return offset
