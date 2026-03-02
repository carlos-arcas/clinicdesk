from __future__ import annotations

from datetime import datetime

import logging
import sqlite3

from clinicdesk.app.application.historial_paciente.usecases import ResumenRaw

logger = logging.getLogger(__name__)


class HistorialListadosQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def buscar_historial_citas(
        self,
        paciente_id: int,
        desde: datetime | None,
        hasta: datetime | None,
        texto: str | None,
        estados: tuple[str, ...] | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]:
        where_sql, params = _build_where_citas(paciente_id, desde, hasta, texto, estados)
        rows = self._run_rows(self._sql_citas(where_sql), (*params, limit, offset), evento="buscar_historial_citas")
        total = self._run_count(self._sql_count_citas(where_sql), params, evento="count_historial_citas")
        return rows, total

    def buscar_historial_recetas(
        self,
        paciente_id: int,
        desde: datetime | None,
        hasta: datetime | None,
        texto: str | None,
        estados: tuple[str, ...] | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]:
        where_sql, params = _build_where_recetas(paciente_id, desde, hasta, texto, estados)
        rows = self._run_rows(self._sql_recetas(where_sql), (*params, limit, offset), evento="buscar_historial_recetas")
        total = self._run_count(self._sql_count_recetas(where_sql), params, evento="count_historial_recetas")
        return rows, total

    def obtener_resumen_historial(
        self,
        paciente_id: int,
        desde: datetime | None,
        hasta: datetime | None,
    ) -> ResumenRaw:
        where_citas, params_citas = _build_where_citas(paciente_id, desde, hasta, None, None)
        where_recetas, params_recetas = _build_where_recetas(paciente_id, desde, hasta, None, None)
        sql = (
            "SELECT "
            f"(SELECT COUNT(*) FROM citas c {where_citas}) AS total_citas, "
            f"(SELECT COUNT(*) FROM citas c {where_citas} AND c.estado = 'NO_PRESENTADO') AS no_presentados, "
            f"(SELECT COUNT(*) FROM recetas r {where_recetas}) AS total_recetas, "
            f"(SELECT COUNT(*) FROM recetas r {where_recetas} AND UPPER(r.estado) NOT IN ('ANULADA','CANCELADA','FINALIZADA','DISPENSADA')) AS recetas_activas"
        )
        params = (*params_citas, *params_citas, *params_recetas, *params_recetas)
        try:
            row = self._connection.execute(sql, params).fetchone()
        except sqlite3.Error as exc:
            logger.error("obtener_resumen_historial_failed", extra={"paciente_id": paciente_id, "error": str(exc)})
            return ResumenRaw(0, 0, 0, 0)
        return ResumenRaw(
            total_citas=int(row["total_citas"] or 0),
            no_presentados=int(row["no_presentados"] or 0),
            total_recetas=int(row["total_recetas"] or 0),
            recetas_activas=int(row["recetas_activas"] or 0),
        )

    def _run_rows(self, sql: str, params: tuple[object, ...], evento: str) -> list[dict[str, object]]:
        try:
            rows = self._connection.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error(f"{evento}_failed", extra={"error": str(exc)})
            return []
        return [dict(row) for row in rows]

    def _run_count(self, sql: str, params: tuple[object, ...], evento: str) -> int:
        try:
            row = self._connection.execute(sql, params).fetchone()
        except sqlite3.Error as exc:
            logger.error(f"{evento}_failed", extra={"error": str(exc)})
            return 0
        return int(row["total"] or 0)

    @staticmethod
    def _sql_citas(where_sql: str) -> str:
        return (
            "SELECT c.id AS cita_id, c.inicio, c.fin, c.estado, "
            "(m.nombre || ' ' || m.apellidos) AS medico, "
            "COALESCE(c.notas, '') AS resumen, "
            "CASE WHEN EXISTS (SELECT 1 FROM incidencias i WHERE i.cita_id = c.id AND i.activo = 1) THEN 1 ELSE 0 END AS tiene_incidencias "
            "FROM citas c JOIN medicos m ON m.id = c.medico_id "
            f"{where_sql} "
            "ORDER BY c.inicio DESC, c.id DESC LIMIT ? OFFSET ?"
        )

    @staticmethod
    def _sql_count_citas(where_sql: str) -> str:
        return f"SELECT COUNT(*) AS total FROM citas c {where_sql}"

    @staticmethod
    def _sql_recetas(where_sql: str) -> str:
        return (
            "SELECT r.id AS receta_id, r.fecha AS receta_fecha, r.estado AS receta_estado, "
            "(m.nombre || ' ' || m.apellidos) AS medico_nombre, "
            "COALESCE(r.observaciones, '') AS observaciones, "
            "COUNT(rl.id) AS num_lineas, "
            "CASE WHEN UPPER(r.estado) IN ('ANULADA','CANCELADA','FINALIZADA','DISPENSADA') THEN 0 ELSE 1 END AS activa "
            "FROM recetas r "
            "JOIN medicos m ON m.id = r.medico_id "
            "LEFT JOIN receta_lineas rl ON rl.receta_id = r.id AND rl.activo = 1 "
            f"{where_sql} "
            "GROUP BY r.id, r.fecha, r.estado, medico_nombre, observaciones "
            "ORDER BY r.fecha DESC, r.id DESC LIMIT ? OFFSET ?"
        )

    @staticmethod
    def _sql_count_recetas(where_sql: str) -> str:
        return f"SELECT COUNT(*) AS total FROM recetas r {where_sql}"


def _build_where_citas(
    paciente_id: int,
    desde: datetime | None,
    hasta: datetime | None,
    texto: str | None,
    estados: tuple[str, ...] | None,
) -> tuple[str, tuple[object, ...]]:
    filtros = ["c.activo = 1", "c.paciente_id = ?"]
    params: list[object] = [paciente_id]
    if desde is not None:
        filtros.append("c.inicio >= ?")
        params.append(desde.isoformat(sep=" "))
    if hasta is not None:
        filtros.append("c.inicio <= ?")
        params.append(hasta.isoformat(sep=" "))
    if texto:
        like = f"%{texto}%"
        filtros.append("(c.notas LIKE ? OR m.nombre LIKE ? OR m.apellidos LIKE ?)")
        params.extend([like, like, like])
    if estados:
        placeholders = ",".join("?" for _ in estados)
        filtros.append(f"c.estado IN ({placeholders})")
        params.extend(estados)
    return "WHERE " + " AND ".join(filtros), tuple(params)


def _build_where_recetas(
    paciente_id: int,
    desde: datetime | None,
    hasta: datetime | None,
    texto: str | None,
    estados: tuple[str, ...] | None,
) -> tuple[str, tuple[object, ...]]:
    filtros = ["r.activo = 1", "r.paciente_id = ?"]
    params: list[object] = [paciente_id]
    if desde is not None:
        filtros.append("r.fecha >= ?")
        params.append(desde.isoformat(sep=" "))
    if hasta is not None:
        filtros.append("r.fecha <= ?")
        params.append(hasta.isoformat(sep=" "))
    if texto:
        like = f"%{texto}%"
        filtros.append("(r.observaciones LIKE ? OR m.nombre LIKE ? OR m.apellidos LIKE ?)")
        params.extend([like, like, like])
    if estados:
        placeholders = ",".join("?" for _ in estados)
        filtros.append(f"r.estado IN ({placeholders})")
        params.extend(estados)
    return "WHERE " + " AND ".join(filtros), tuple(params)
