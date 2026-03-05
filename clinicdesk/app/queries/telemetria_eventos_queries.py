from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo

LOGGER = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TopEventoTelemetriaQuery:
    evento: str
    total: int


class TelemetriaEventosQueries:
    def __init__(self, proveedor: ProveedorConexionSqlitePorHilo | sqlite3.Connection) -> None:
        self._proveedor = proveedor

    def _con(self) -> sqlite3.Connection:
        return self._proveedor if isinstance(self._proveedor, sqlite3.Connection) else self._proveedor.obtener()

    def top_eventos_por_rango(
        self,
        desde_utc: str | datetime,
        hasta_utc: str | datetime,
        limit: int = 5,
    ) -> list[TopEventoTelemetriaQuery]:
        try:
            rows = (
                self._con()
                .execute(
                    """
                SELECT evento, COUNT(*) AS total
                FROM telemetria_eventos
                WHERE datetime(timestamp_utc) >= datetime(?)
                  AND datetime(timestamp_utc) <= datetime(?)
                GROUP BY evento
                ORDER BY total DESC, evento ASC
                LIMIT ?
                """,
                    (_to_iso(desde_utc), _to_iso(hasta_utc), limit),
                )
                .fetchall()
            )
        except sqlite3.DatabaseError:
            LOGGER.exception("telemetria_top_eventos_query_error")
            return []
        return [TopEventoTelemetriaQuery(evento=str(row["evento"]), total=int(row["total"])) for row in rows]


def _to_iso(valor: str | datetime) -> str:
    return valor.isoformat() if isinstance(valor, datetime) else valor
