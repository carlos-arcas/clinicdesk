from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


_PRESETS_VALIDOS = {"HOY", "SEMANA", "MES", "PERSONALIZADO"}
_RIESGO_VALIDO = {"TODOS", "ALTO_MEDIO", "SOLO_ALTO"}
_RECORDATORIO_VALIDO = {"TODOS", "SIN_PREPARAR", "NO_ENVIADO"}
_ESTADOS_VALIDOS = {
    "PROGRAMADA",
    "CONFIRMADA",
    "CANCELADA",
    "REALIZADA",
    "NO_PRESENTADO",
}


@dataclass(frozen=True, slots=True)
class FiltrosCitasDTO:
    rango_preset: str = "HOY"
    desde: datetime | None = None
    hasta: datetime | None = None
    texto_busqueda: str | None = None
    estado: str | None = None
    medico_id: int | None = None
    sala_id: int | None = None
    paciente_id: int | None = None
    riesgo_filtro: str | None = None
    recordatorio_filtro: str | None = None


def normalizar_filtros_citas(filtros: FiltrosCitasDTO, ahora: datetime) -> FiltrosCitasDTO:
    preset = _normalizar_preset(filtros.rango_preset)
    desde, hasta = _resolver_rango(preset, filtros.desde, filtros.hasta, ahora)
    return FiltrosCitasDTO(
        rango_preset=preset,
        desde=desde,
        hasta=hasta,
        texto_busqueda=_normalizar_texto(filtros.texto_busqueda),
        estado=_normalizar_estado(filtros.estado),
        medico_id=_normalizar_id(filtros.medico_id),
        sala_id=_normalizar_id(filtros.sala_id),
        paciente_id=_normalizar_id(filtros.paciente_id),
        riesgo_filtro=_normalizar_catalogo(filtros.riesgo_filtro, _RIESGO_VALIDO),
        recordatorio_filtro=_normalizar_catalogo(filtros.recordatorio_filtro, _RECORDATORIO_VALIDO),
    )


def _normalizar_preset(preset: str) -> str:
    preset_norm = (preset or "").strip().upper()
    if preset_norm in _PRESETS_VALIDOS:
        return preset_norm
    return "HOY"


def _resolver_rango(
    preset: str,
    desde: datetime | None,
    hasta: datetime | None,
    ahora: datetime,
) -> tuple[datetime, datetime]:
    if preset == "PERSONALIZADO" and desde and hasta:
        return _ordenar_y_limitar(desde, hasta)

    if preset == "SEMANA":
        inicio = datetime(ahora.year, ahora.month, ahora.day)
        return _ordenar_y_limitar(inicio, inicio + timedelta(days=6, hours=23, minutes=59, seconds=59))

    if preset == "MES":
        inicio = datetime(ahora.year, ahora.month, 1)
        if ahora.month == 12:
            siguiente = datetime(ahora.year + 1, 1, 1)
        else:
            siguiente = datetime(ahora.year, ahora.month + 1, 1)
        return _ordenar_y_limitar(inicio, siguiente - timedelta(seconds=1))

    inicio_hoy = datetime(ahora.year, ahora.month, ahora.day)
    return _ordenar_y_limitar(inicio_hoy, inicio_hoy + timedelta(hours=23, minutes=59, seconds=59))


def _ordenar_y_limitar(desde: datetime, hasta: datetime) -> tuple[datetime, datetime]:
    if desde > hasta:
        desde, hasta = hasta, desde
    limite = desde + timedelta(days=366)
    if hasta > limite:
        hasta = limite
    return desde, hasta


def _normalizar_texto(texto: str | None) -> str | None:
    texto_norm = (texto or "").strip()
    return texto_norm or None


def _normalizar_estado(estado: str | None) -> str | None:
    estado_norm = (estado or "").strip().upper()
    if not estado_norm or estado_norm == "TODOS":
        return None
    if estado_norm in _ESTADOS_VALIDOS:
        return estado_norm
    return None


def _normalizar_id(valor: int | None) -> int | None:
    if valor is None:
        return None
    if valor <= 0:
        return None
    return valor


def _normalizar_catalogo(valor: str | None, opciones: set[str]) -> str | None:
    if valor is None:
        return None
    valor_norm = valor.strip().upper()
    if not valor_norm:
        return None
    if valor_norm in opciones:
        return valor_norm
    return None
