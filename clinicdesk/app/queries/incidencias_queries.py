from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import like_value, normalize_search_text


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IncidenciaRow:
    id: int
    tipo: str
    severidad: str
    estado: str
    fecha_hora: str
    descripcion: str
    nota_override: str
    confirmado_por_personal_id: int
    confirmado_por_nombre: str

    medico_id: Optional[int]
    medico_nombre: Optional[str]
    personal_id: Optional[int]
    personal_nombre: Optional[str]

    cita_id: Optional[int]
    receta_id: Optional[int]
    dispensacion_id: Optional[int]


@dataclass(frozen=True, slots=True)
class _IncidenciasListParams:
    tipo: Optional[str]
    estado: Optional[str]
    severidad: Optional[str]
    fecha_desde: Optional[str]
    fecha_hasta: Optional[str]
    texto: Optional[str]


class IncidenciasQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def list(
        self,
        *,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        severidad: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        texto: Optional[str] = None,
        limit: int = 500,
    ) -> List[IncidenciaRow]:
        params = _IncidenciasListParams(
            tipo=normalize_search_text(tipo),
            estado=normalize_search_text(estado),
            severidad=normalize_search_text(severidad),
            fecha_desde=normalize_search_text(fecha_desde),
            fecha_hasta=normalize_search_text(fecha_hasta),
            texto=normalize_search_text(texto),
        )
        where_sql = self._build_where(params)
        sql_params = (*self._build_params(params), int(limit))

        try:
            rows = self._conn.execute(
                f"""
                SELECT
                    i.id,
                    i.tipo,
                    i.severidad,
                    i.estado,
                    i.fecha_hora,
                    i.descripcion,
                    i.nota_override,
                    i.confirmado_por_personal_id,
                    (cp.nombre || ' ' || cp.apellidos) AS confirmado_por_nombre,

                    i.medico_id,
                    CASE WHEN i.medico_id IS NULL THEN NULL ELSE (m.nombre || ' ' || m.apellidos) END AS medico_nombre,

                    i.personal_id,
                    CASE WHEN i.personal_id IS NULL THEN NULL ELSE (p.nombre || ' ' || p.apellidos) END AS personal_nombre,

                    i.cita_id,
                    i.receta_id,
                    i.dispensacion_id
                FROM incidencias i
                LEFT JOIN medicos m ON m.id = i.medico_id
                LEFT JOIN personal p ON p.id = i.personal_id
                JOIN personal cp ON cp.id = i.confirmado_por_personal_id
                {where_sql}
                ORDER BY i.fecha_hora DESC, i.id DESC
                LIMIT ?
                """,
                sql_params,
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en IncidenciasQueries.list: %s", exc)
            return []

        return [self._row_to_model(row) for row in rows]

    def _build_where(self, params: _IncidenciasListParams) -> str:
        clauses = ["i.activo = 1"]
        if params.tipo:
            clauses.append("i.tipo LIKE ? COLLATE NOCASE")
        if params.estado:
            clauses.append("i.estado LIKE ? COLLATE NOCASE")
        if params.severidad:
            clauses.append("i.severidad LIKE ? COLLATE NOCASE")
        if params.fecha_desde:
            clauses.append("i.fecha_hora >= ?")
        if params.fecha_hasta:
            clauses.append("i.fecha_hora <= ?")
        if params.texto:
            clauses.append(
                "(i.descripcion LIKE ? COLLATE NOCASE OR i.nota_override LIKE ? COLLATE NOCASE "
                "OR cp.nombre LIKE ? COLLATE NOCASE OR cp.apellidos LIKE ? COLLATE NOCASE)"
            )
        return "WHERE " + " AND ".join(clauses)

    def _build_params(self, params: _IncidenciasListParams) -> List[object]:
        out: List[object] = []
        if params.tipo:
            out.append(like_value(params.tipo))
        if params.estado:
            out.append(like_value(params.estado))
        if params.severidad:
            out.append(like_value(params.severidad))
        if params.fecha_desde:
            out.append(f"{params.fecha_desde} 00:00:00")
        if params.fecha_hasta:
            out.append(f"{params.fecha_hasta} 23:59:59")
        if params.texto:
            like = like_value(params.texto)
            out.extend([like, like, like, like])
        return out

    def _row_to_model(self, row: sqlite3.Row) -> IncidenciaRow:
        return IncidenciaRow(
            id=int(row["id"]),
            tipo=row["tipo"],
            severidad=row["severidad"],
            estado=row["estado"],
            fecha_hora=row["fecha_hora"],
            descripcion=row["descripcion"],
            nota_override=row["nota_override"],
            confirmado_por_personal_id=int(row["confirmado_por_personal_id"]),
            confirmado_por_nombre=row["confirmado_por_nombre"],
            medico_id=row["medico_id"],
            medico_nombre=row["medico_nombre"],
            personal_id=row["personal_id"],
            personal_nombre=row["personal_nombre"],
            cita_id=row["cita_id"],
            receta_id=row["receta_id"],
            dispensacion_id=row["dispensacion_id"],
        )

    def get_by_id(self, incidencia_id: int) -> Optional[IncidenciaRow]:
        try:
            row = self._conn.execute(
                """
                SELECT
                    i.id,
                    i.tipo,
                    i.severidad,
                    i.estado,
                    i.fecha_hora,
                    i.descripcion,
                    i.nota_override,
                    i.confirmado_por_personal_id,
                    (cp.nombre || ' ' || cp.apellidos) AS confirmado_por_nombre,

                    i.medico_id,
                    CASE WHEN i.medico_id IS NULL THEN NULL ELSE (m.nombre || ' ' || m.apellidos) END AS medico_nombre,

                    i.personal_id,
                    CASE WHEN i.personal_id IS NULL THEN NULL ELSE (p.nombre || ' ' || p.apellidos) END AS personal_nombre,

                    i.cita_id,
                    i.receta_id,
                    i.dispensacion_id
                FROM incidencias i
                LEFT JOIN medicos m ON m.id = i.medico_id
                LEFT JOIN personal p ON p.id = i.personal_id
                JOIN personal cp ON cp.id = i.confirmado_por_personal_id
                WHERE i.id = ? AND i.activo = 1
                """,
                (incidencia_id,),
            ).fetchone()
        except sqlite3.Error as exc:
            logger.error("Error SQL en IncidenciasQueries.get_by_id: %s", exc)
            return None

        if not row:
            return None
        return self._row_to_model(row)
