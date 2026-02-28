from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import like_value, normalize_search_text


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DispensacionRow:
    id: int
    fecha_hora: str
    paciente: str
    personal: str
    medicamento: str
    cantidad: int
    receta_id: int
    incidencia: bool


@dataclass(frozen=True, slots=True)
class _DispensacionesParams:
    fecha_desde: Optional[str]
    fecha_hasta: Optional[str]
    paciente_texto: Optional[str]
    personal_texto: Optional[str]
    medicamento_texto: Optional[str]


class DispensacionesQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def list(
        self,
        *,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        paciente_texto: Optional[str] = None,
        personal_texto: Optional[str] = None,
        medicamento_texto: Optional[str] = None,
        limit: int = 500,
    ) -> List[DispensacionRow]:
        params = _DispensacionesParams(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            paciente_texto=normalize_search_text(paciente_texto),
            personal_texto=normalize_search_text(personal_texto),
            medicamento_texto=normalize_search_text(medicamento_texto),
        )
        where_sql = self._build_where(params)
        sql_params = (*self._build_params(params), int(limit))

        try:
            rows = self._conn.execute(
                f"""
                SELECT d.id, d.fecha_hora,
                       (p.nombre || ' ' || p.apellidos) AS paciente,
                       (per.nombre || ' ' || per.apellidos) AS personal,
                       m.nombre_comercial AS medicamento,
                       d.cantidad, d.receta_id,
                       EXISTS(
                           SELECT 1
                           FROM incidencias i
                           WHERE i.dispensacion_id = d.id
                             AND i.activo = 1
                       ) AS incidencia
                FROM dispensaciones d
                JOIN recetas r ON r.id = d.receta_id
                JOIN pacientes p ON p.id = r.paciente_id
                JOIN personal per ON per.id = d.personal_id
                JOIN medicamentos m ON m.id = d.medicamento_id
                {where_sql}
                ORDER BY d.fecha_hora DESC
                LIMIT ?
                """,
                sql_params,
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en DispensacionesQueries.list: %s", exc)
            return []

        return [self._row_to_model(row) for row in rows]

    def _build_where(self, params: _DispensacionesParams) -> str:
        clauses = [
            *self._date_clauses(params),
            *self._paciente_clauses(params),
            *self._personal_clauses(params),
            *self._medicamento_clauses(params),
            "d.activo = 1",
            "r.activo = 1",
        ]
        return "WHERE " + " AND ".join(clauses)

    def _build_params(self, params: _DispensacionesParams) -> List[object]:
        out: List[object] = []
        if params.fecha_desde:
            out.append(f"{params.fecha_desde} 00:00:00")
        if params.fecha_hasta:
            out.append(f"{params.fecha_hasta} 23:59:59")
        if params.paciente_texto:
            like = like_value(params.paciente_texto)
            out.extend([like, like, like, like])
        if params.personal_texto:
            like = like_value(params.personal_texto)
            out.extend([like, like, like, like, like])
        if params.medicamento_texto:
            like = like_value(params.medicamento_texto)
            out.extend([like, like])
        return out

    def _row_to_model(self, row: sqlite3.Row) -> DispensacionRow:
        return DispensacionRow(
            id=row["id"],
            fecha_hora=row["fecha_hora"],
            paciente=row["paciente"],
            personal=row["personal"],
            medicamento=row["medicamento"],
            cantidad=int(row["cantidad"]),
            receta_id=row["receta_id"],
            incidencia=bool(row["incidencia"]),
        )

    def _date_clauses(self, params: _DispensacionesParams) -> List[str]:
        clauses: List[str] = []
        if params.fecha_desde:
            clauses.append("d.fecha_hora >= ?")
        if params.fecha_hasta:
            clauses.append("d.fecha_hora <= ?")
        return clauses

    def _paciente_clauses(self, params: _DispensacionesParams) -> List[str]:
        if not params.paciente_texto:
            return []
        return [
            "(p.nombre LIKE ? COLLATE NOCASE OR p.apellidos LIKE ? COLLATE NOCASE "
            "OR p.documento LIKE ? COLLATE NOCASE OR p.telefono LIKE ? COLLATE NOCASE)"
        ]

    def _personal_clauses(self, params: _DispensacionesParams) -> List[str]:
        if not params.personal_texto:
            return []
        return [
            "(per.nombre LIKE ? COLLATE NOCASE OR per.apellidos LIKE ? COLLATE NOCASE "
            "OR per.documento LIKE ? COLLATE NOCASE OR per.telefono LIKE ? COLLATE NOCASE "
            "OR per.puesto LIKE ? COLLATE NOCASE)"
        ]

    def _medicamento_clauses(self, params: _DispensacionesParams) -> List[str]:
        if not params.medicamento_texto:
            return []
        return [
            "(m.nombre_comercial LIKE ? COLLATE NOCASE OR m.nombre_compuesto LIKE ? COLLATE NOCASE)"
        ]
