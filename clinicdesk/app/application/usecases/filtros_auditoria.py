from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from clinicdesk.app.queries.auditoria_accesos_queries import FiltrosAuditoriaAccesos


PRESET_HOY = "hoy"
PRESET_7_DIAS = "7_dias"
PRESET_30_DIAS = "30_dias"
PRESET_PERSONALIZADO = "personalizado"


def aplicar_preset_rango_auditoria(
    filtros: FiltrosAuditoriaAccesos,
    preset: str | None,
    ahora: datetime | None = None,
) -> FiltrosAuditoriaAccesos:
    if preset in (None, PRESET_PERSONALIZADO):
        return filtros
    now_utc = _resolver_ahora_utc(ahora)
    desde, hasta = _calcular_rango_por_preset(preset, now_utc)
    return FiltrosAuditoriaAccesos(
        usuario_contiene=filtros.usuario_contiene,
        accion=filtros.accion,
        entidad_tipo=filtros.entidad_tipo,
        desde_utc=desde,
        hasta_utc=hasta,
    )


def _calcular_rango_por_preset(preset: str, ahora_utc: datetime) -> tuple[datetime | None, datetime | None]:
    if preset == PRESET_HOY:
        return _rango_dia(ahora_utc.date())
    if preset == PRESET_7_DIAS:
        return _rango_dias_hasta_hoy(7, ahora_utc)
    if preset == PRESET_30_DIAS:
        return _rango_dias_hasta_hoy(30, ahora_utc)
    return None, None


def _resolver_ahora_utc(ahora: datetime | None) -> datetime:
    if ahora is None:
        return datetime.now(UTC)
    if ahora.tzinfo is None:
        return ahora.replace(tzinfo=UTC)
    return ahora.astimezone(UTC)


def _rango_dias_hasta_hoy(cantidad_dias: int, ahora_utc: datetime) -> tuple[datetime, datetime]:
    dia_inicio = ahora_utc.date() - timedelta(days=max(0, cantidad_dias - 1))
    return _rango_dia(dia_inicio, dia_fin=ahora_utc.date())


def _rango_dia(dia_inicio: date, dia_fin: date | None = None) -> tuple[datetime, datetime]:
    fin = dia_fin or dia_inicio
    desde = datetime.combine(dia_inicio, time.min, tzinfo=UTC)
    hasta = datetime.combine(fin, time.max, tzinfo=UTC)
    return desde, hasta
