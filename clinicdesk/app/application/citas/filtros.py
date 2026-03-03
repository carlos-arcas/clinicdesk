from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


_PRESETS_VALIDOS = {"HOY", "SEMANA", "MES", "PERSONALIZADO"}
_RECORDATORIO_VALIDO = {"TODOS", "SIN_PREPARAR", "NO_ENVIADO"}
_FILTROS_CALIDAD_VALIDOS = {"SIN_CHECKIN", "SIN_INICIO_FIN", "SIN_SALIDA"}
_ESTADOS_VALIDOS = {
    "PROGRAMADA",
    "CONFIRMADA",
    "CANCELADA",
    "REALIZADA",
    "NO_PRESENTADO",
}
_LIMIT_POR_DEFECTO = 50
_OFFSET_POR_DEFECTO = 0
_LIMIT_MAXIMO = 200


@dataclass(frozen=True, slots=True)
class FiltrosCitasDTO:
    rango_preset: str = "HOY"
    desde: datetime | None = None
    hasta: datetime | None = None
    texto_busqueda: str | None = None
    estado_cita: str | None = None
    medico_id: int | None = None
    sala_id: int | None = None
    paciente_id: int | None = None
    incluir_riesgo: bool = False
    recordatorio_filtro: str | None = None
    filtro_calidad: str | None = None
    limit: int = _LIMIT_POR_DEFECTO
    offset: int = _OFFSET_POR_DEFECTO

    @property
    def estado(self) -> str | None:
        return self.estado_cita


def normalizar_filtros_citas(filtros: FiltrosCitasDTO, ahora: datetime) -> FiltrosCitasDTO:
    preset = _normalizar_preset(filtros.rango_preset)
    desde, hasta = _resolver_rango(preset, filtros.desde, filtros.hasta, ahora)
    return FiltrosCitasDTO(
        rango_preset=preset,
        desde=desde,
        hasta=hasta,
        texto_busqueda=_normalizar_texto(filtros.texto_busqueda),
        estado_cita=_normalizar_estado(filtros.estado_cita or filtros.estado),
        medico_id=_normalizar_id(filtros.medico_id),
        sala_id=_normalizar_id(filtros.sala_id),
        paciente_id=_normalizar_id(filtros.paciente_id),
        incluir_riesgo=bool(filtros.incluir_riesgo),
        recordatorio_filtro=_normalizar_catalogo(filtros.recordatorio_filtro, _RECORDATORIO_VALIDO),
        filtro_calidad=_normalizar_catalogo(filtros.filtro_calidad, _FILTROS_CALIDAD_VALIDOS),
        limit=_normalizar_limit(filtros.limit),
        offset=_normalizar_offset(filtros.offset),
    )


def _normalizar_preset(preset: str) -> str:
    valor = (preset or "").strip().upper()
    return valor if valor in _PRESETS_VALIDOS else "HOY"


def _resolver_rango(
    preset: str,
    desde: datetime | None,
    hasta: datetime | None,
    ahora: datetime,
) -> tuple[datetime, datetime]:
    if preset == "PERSONALIZADO" and desde and hasta:
        return _ordenar_rango(desde, hasta)
    if preset == "SEMANA":
        inicio = _inicio_dia(ahora)
        return inicio, inicio + timedelta(days=6, hours=23, minutes=59, seconds=59)
    if preset == "MES":
        inicio = datetime(ahora.year, ahora.month, 1)
        siguiente = datetime(ahora.year + (ahora.month // 12), ((ahora.month % 12) + 1), 1)
        return inicio, siguiente - timedelta(seconds=1)
    inicio = _inicio_dia(ahora)
    return inicio, inicio + timedelta(hours=23, minutes=59, seconds=59)


def _inicio_dia(fecha: datetime) -> datetime:
    return datetime(fecha.year, fecha.month, fecha.day)


def _ordenar_rango(desde: datetime, hasta: datetime) -> tuple[datetime, datetime]:
    return (hasta, desde) if desde > hasta else (desde, hasta)


def _normalizar_texto(texto: str | None) -> str | None:
    valor = (texto or "").strip()
    return valor or None


def redactar_texto_busqueda(texto: str | None) -> str | None:
    if texto is None:
        return None
    valor = texto.strip()
    if not valor:
        return None
    if len(valor) <= 12:
        return valor
    return f"{valor[:12]}…"


def _normalizar_estado(estado: str | None) -> str | None:
    valor = (estado or "").strip().upper()
    if not valor or valor == "TODOS":
        return None
    return valor if valor in _ESTADOS_VALIDOS else None


def _normalizar_id(valor: int | None) -> int | None:
    return valor if isinstance(valor, int) and valor > 0 else None


def _normalizar_catalogo(valor: str | None, opciones: set[str]) -> str | None:
    valor_norm = (valor or "").strip().upper()
    if not valor_norm or valor_norm == "TODOS":
        return None
    return valor_norm if valor_norm in opciones else None


def _normalizar_limit(limit: int | None) -> int:
    if not isinstance(limit, int) or limit <= 0:
        return _LIMIT_POR_DEFECTO
    return min(limit, _LIMIT_MAXIMO)


def _normalizar_offset(offset: int | None) -> int:
    if not isinstance(offset, int) or offset < 0:
        return _OFFSET_POR_DEFECTO
    return offset
