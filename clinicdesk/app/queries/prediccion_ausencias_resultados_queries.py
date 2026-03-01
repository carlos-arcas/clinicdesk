from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from datetime import datetime, timezone
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo


_ESTADOS_CERRADOS = ("REALIZADA", "NO_PRESENTADO")
_RIESGOS_VALIDOS = ("BAJO", "MEDIO", "ALTO")


@dataclass(frozen=True, slots=True)
class ItemRegistroPrediccionAusencia:
    cita_id: int
    riesgo: str
    timestamp_utc: str
    source: str


@dataclass(frozen=True, slots=True)
class FilaResultadoRecientePrediccion:
    riesgo: str
    total_predichas: int
    total_no_vino: int
    total_vino: int


@dataclass(frozen=True, slots=True)
class ResultadoRecientePrediccion:
    version_modelo_fecha_utc: str | None
    filas: tuple[FilaResultadoRecientePrediccion, ...]


class PrediccionAusenciasResultadosQueries:
    def __init__(
        self,
        proveedor_conexion: ProveedorConexionSqlitePorHilo | sqlite3.Connection,
    ) -> None:
        self._proveedor_conexion = proveedor_conexion

    def _con(self) -> sqlite3.Connection:
        if isinstance(self._proveedor_conexion, sqlite3.Connection):
            return self._proveedor_conexion
        return self._proveedor_conexion.obtener()

    def registrar_predicciones_ausencias(
        self,
        modelo_fecha_utc: str,
        items: list[ItemRegistroPrediccionAusencia],
    ) -> int:
        filas = [
            (item.timestamp_utc, modelo_fecha_utc, item.cita_id, item.riesgo, item.source)
            for item in items
            if item.riesgo in _RIESGOS_VALIDOS
        ]
        if not filas:
            return 0
        cursor = self._con().executemany(
            """
            INSERT OR IGNORE INTO predicciones_ausencias_log(
                timestamp_utc,
                modelo_fecha_utc,
                cita_id,
                riesgo,
                source
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            filas,
        )
        return cursor.rowcount if cursor.rowcount is not None else 0

    def obtener_resultados_recientes_prediccion(self, ventana_dias: int = 60) -> ResultadoRecientePrediccion:
        version = self._obtener_version_objetivo()
        if version is None:
            return ResultadoRecientePrediccion(version_modelo_fecha_utc=None, filas=tuple())
        rows = self._con().execute(
            """
            SELECT
                pl.riesgo AS riesgo,
                COUNT(1) AS total_predichas,
                SUM(CASE WHEN c.estado = 'NO_PRESENTADO' THEN 1 ELSE 0 END) AS total_no_vino,
                SUM(CASE WHEN c.estado = 'REALIZADA' THEN 1 ELSE 0 END) AS total_vino
            FROM predicciones_ausencias_log pl
            JOIN citas c ON c.id = pl.cita_id
            WHERE pl.modelo_fecha_utc = ?
              AND pl.riesgo IN ('BAJO', 'MEDIO', 'ALTO')
              AND c.activo = 1
              AND c.estado IN (?, ?)
              AND datetime(c.inicio) >= datetime('now', ?)
            GROUP BY pl.riesgo
            """,
            (version, *_ESTADOS_CERRADOS, f"-{ventana_dias} days"),
        ).fetchall()
        return ResultadoRecientePrediccion(
            version_modelo_fecha_utc=version,
            filas=tuple(
                FilaResultadoRecientePrediccion(
                    riesgo=str(row["riesgo"]),
                    total_predichas=int(row["total_predichas"] or 0),
                    total_no_vino=int(row["total_no_vino"] or 0),
                    total_vino=int(row["total_vino"] or 0),
                )
                for row in rows
            ),
        )

    def _obtener_version_objetivo(self) -> str | None:
        row = self._con().execute("SELECT MAX(modelo_fecha_utc) AS version FROM predicciones_ausencias_log").fetchone()
        if row is None or row["version"] is None:
            return None
        return str(row["version"])


def ahora_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
