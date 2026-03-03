from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import sqlite3

from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo

_ESTADOS_CERRADOS = ("REALIZADA", "NO_PRESENTADO", "CANCELADA")


@dataclass(frozen=True, slots=True)
class FaltantesCalidadDatos:
    faltan_check_in: int
    faltan_inicio_fin: int
    faltan_check_out: int


class CalidadDatosQueries:
    """Consultas de calidad de hitos para citas cerradas en un periodo."""

    def __init__(self, proveedor: ProveedorConexionSqlitePorHilo | sqlite3.Connection) -> None:
        self._proveedor = proveedor

    def _con(self) -> sqlite3.Connection:
        return self._proveedor if isinstance(self._proveedor, sqlite3.Connection) else self._proveedor.obtener()

    def contar_citas_cerradas(self, desde: date, hasta: date) -> int:
        query = """
            SELECT COUNT(1) AS total
            FROM citas c
            WHERE c.activo = 1
              AND c.estado IN (?, ?, ?)
              AND date(c.inicio) BETWEEN date(?) AND date(?)
        """
        row = self._con().execute(query, (*_ESTADOS_CERRADOS, desde.isoformat(), hasta.isoformat())).fetchone()
        return int(row["total"] if row else 0)

    def contar_completas(self, desde: date, hasta: date) -> int:
        query = """
            SELECT COUNT(1) AS total
            FROM citas c
            WHERE c.activo = 1
              AND c.estado IN (?, ?, ?)
              AND date(c.inicio) BETWEEN date(?) AND date(?)
              AND c.check_in_at IS NOT NULL
              AND c.consulta_inicio_at IS NOT NULL
              AND c.consulta_fin_at IS NOT NULL
              AND c.check_out_at IS NOT NULL
        """
        row = self._con().execute(query, (*_ESTADOS_CERRADOS, desde.isoformat(), hasta.isoformat())).fetchone()
        return int(row["total"] if row else 0)

    def contar_faltantes(self, desde: date, hasta: date) -> FaltantesCalidadDatos:
        query = """
            SELECT
                SUM(CASE WHEN c.check_in_at IS NULL THEN 1 ELSE 0 END) AS faltan_check_in,
                SUM(CASE WHEN c.consulta_inicio_at IS NULL OR c.consulta_fin_at IS NULL THEN 1 ELSE 0 END) AS faltan_inicio_fin,
                SUM(CASE WHEN c.check_out_at IS NULL THEN 1 ELSE 0 END) AS faltan_check_out
            FROM citas c
            WHERE c.activo = 1
              AND c.estado IN (?, ?, ?)
              AND date(c.inicio) BETWEEN date(?) AND date(?)
        """
        row = self._con().execute(query, (*_ESTADOS_CERRADOS, desde.isoformat(), hasta.isoformat())).fetchone()
        return FaltantesCalidadDatos(
            faltan_check_in=int((row or {})["faltan_check_in"] or 0),
            faltan_inicio_fin=int((row or {})["faltan_inicio_fin"] or 0),
            faltan_check_out=int((row or {})["faltan_check_out"] or 0),
        )
