from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import sqlite3

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.common.search_utils import normalize_search_text

LOGGER = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class FiltrosAuditoriaAccesos:
    usuario_contiene: str | None = None
    accion: str | None = None
    entidad_tipo: str | None = None
    desde_utc: str | datetime | None = None
    hasta_utc: str | datetime | None = None


@dataclass(frozen=True, slots=True)
class AuditoriaAccesoItemQuery:
    timestamp_utc: str
    usuario: str
    modo_demo: bool
    accion: str
    entidad_tipo: str
    entidad_id: str


class AuditoriaAccesosQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def buscar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditoriaAccesoItemQuery], int]:
        where_sql, where_params = _build_where_sql(filtros)
        limit_value = max(1, int(limit))
        offset_value = max(0, int(offset))
        items = self._buscar_items(where_sql, where_params, limit_value, offset_value)
        total = self._contar_items(where_sql, where_params)
        return items, total

    def _buscar_items(
        self,
        where_sql: str,
        where_params: tuple[Any, ...],
        limit: int,
        offset: int,
    ) -> list[AuditoriaAccesoItemQuery]:
        sql = (
            "SELECT timestamp_utc, usuario, modo_demo, accion, entidad_tipo, entidad_id "
            "FROM auditoria_accesos "
            f"{where_sql} "
            "ORDER BY timestamp_utc DESC "
            "LIMIT ? OFFSET ?"
        )
        params = (*where_params, limit, offset)
        try:
            rows = self._connection.execute(sql, params).fetchall()
        except sqlite3.Error:
            LOGGER.exception("auditoria_accesos_query_items_error")
            return []
        return [_map_row(row) for row in rows]

    def _contar_items(self, where_sql: str, where_params: tuple[Any, ...]) -> int:
        sql = f"SELECT COUNT(*) AS total FROM auditoria_accesos {where_sql}"
        try:
            row = self._connection.execute(sql, where_params).fetchone()
        except sqlite3.Error:
            LOGGER.exception("auditoria_accesos_query_count_error")
            return 0
        if row is None:
            return 0
        return int(row["total"])


def buscar_auditoria_accesos(
    connection: sqlite3.Connection,
    filtros: FiltrosAuditoriaAccesos,
    limit: int,
    offset: int,
) -> tuple[list[AuditoriaAccesoItemQuery], int]:
    return AuditoriaAccesosQueries(connection).buscar_auditoria_accesos(filtros, limit, offset)


def _build_where_sql(filtros: FiltrosAuditoriaAccesos) -> tuple[str, tuple[Any, ...]]:
    clauses: list[str] = []
    params: list[Any] = []

    usuario = normalize_search_text(filtros.usuario_contiene)
    accion = normalize_search_text(filtros.accion)
    entidad_tipo = normalize_search_text(filtros.entidad_tipo)
    desde = _to_iso(filtros.desde_utc)
    hasta = _to_iso(filtros.hasta_utc)

    if usuario:
        clauses.append("usuario LIKE ? COLLATE NOCASE")
        params.append(f"%{usuario}%")
    if accion:
        clauses.append("accion = ?")
        params.append(accion)
    if entidad_tipo:
        clauses.append("entidad_tipo = ?")
        params.append(entidad_tipo)
    if desde:
        clauses.append("timestamp_utc >= ?")
        params.append(desde)
    if hasta:
        clauses.append("timestamp_utc <= ?")
        params.append(hasta)

    if not clauses:
        return "", ()
    return f"WHERE {' AND '.join(clauses)}", tuple(params)


def _to_iso(value: str | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    value_str = normalize_search_text(value)
    return value_str


def _map_row(row: sqlite3.Row) -> AuditoriaAccesoItemQuery:
    return AuditoriaAccesoItemQuery(
        timestamp_utc=row["timestamp_utc"],
        usuario=row["usuario"],
        modo_demo=bool(row["modo_demo"]),
        accion=row["accion"],
        entidad_tipo=row["entidad_tipo"],
        entidad_id=row["entidad_id"],
    )
