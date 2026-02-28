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
        clauses = []
        params: List[object] = []

        paciente_texto = normalize_search_text(paciente_texto)
        personal_texto = normalize_search_text(personal_texto)
        medicamento_texto = normalize_search_text(medicamento_texto)

        if fecha_desde:
            clauses.append("d.fecha_hora >= ?")
            params.append(f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            clauses.append("d.fecha_hora <= ?")
            params.append(f"{fecha_hasta} 23:59:59")
        if paciente_texto:
            like = like_value(paciente_texto)
            clauses.append(
                "(p.nombre LIKE ? COLLATE NOCASE OR p.apellidos LIKE ? COLLATE NOCASE "
                "OR p.documento LIKE ? COLLATE NOCASE OR p.telefono LIKE ? COLLATE NOCASE)"
            )
            params.extend([like, like, like, like])
        if personal_texto:
            like = like_value(personal_texto)
            clauses.append(
                "(per.nombre LIKE ? COLLATE NOCASE OR per.apellidos LIKE ? COLLATE NOCASE "
                "OR per.documento LIKE ? COLLATE NOCASE OR per.telefono LIKE ? COLLATE NOCASE "
                "OR per.puesto LIKE ? COLLATE NOCASE)"
            )
            params.extend([like, like, like, like, like])
        if medicamento_texto:
            like = like_value(medicamento_texto)
            clauses.append(
                "(m.nombre_comercial LIKE ? COLLATE NOCASE OR m.nombre_compuesto LIKE ? COLLATE NOCASE)"
            )
            params.extend([like, like])

        clauses.append("d.activo = 1")
        clauses.append("r.activo = 1")
        where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

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
                (*params, int(limit)),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en DispensacionesQueries.list: %s", exc)
            return []

        return [
            DispensacionRow(
                id=row["id"],
                fecha_hora=row["fecha_hora"],
                paciente=row["paciente"],
                personal=row["personal"],
                medicamento=row["medicamento"],
                cantidad=int(row["cantidad"]),
                receta_id=row["receta_id"],
                incidencia=bool(row["incidencia"]),
            )
            for row in rows
        ]
