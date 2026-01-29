from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sqlite3


@dataclass(frozen=True, slots=True)
class CalendarioRow:
    id: int
    fecha: str
    turno: str
    hora_inicio: str
    hora_fin: str
    observaciones: str
    activo: bool


class TurnosQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def list_calendario_medico(
        self,
        medico_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[CalendarioRow]:
        clauses = ["cm.medico_id = ?"]
        params: List[object] = [medico_id]

        if desde:
            clauses.append("cm.fecha >= ?")
            params.append(desde)
        if hasta:
            clauses.append("cm.fecha <= ?")
            params.append(hasta)

        sql = (
            "SELECT cm.id, cm.fecha, t.nombre AS turno, "
            "COALESCE(cm.hora_inicio_override, t.hora_inicio) AS hora_inicio, "
            "COALESCE(cm.hora_fin_override, t.hora_fin) AS hora_fin, "
            "cm.observaciones, cm.activo "
            "FROM calendario_medico cm "
            "JOIN turnos t ON t.id = cm.turno_id "
            "WHERE " + " AND ".join(clauses) + " "
            "ORDER BY cm.fecha"
        )

        rows = self._conn.execute(sql, params).fetchall()
        return [
            CalendarioRow(
                id=row["id"],
                fecha=row["fecha"],
                turno=row["turno"],
                hora_inicio=row["hora_inicio"],
                hora_fin=row["hora_fin"],
                observaciones=row["observaciones"] or "",
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def list_calendario_personal(
        self,
        personal_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[CalendarioRow]:
        clauses = ["cp.personal_id = ?"]
        params: List[object] = [personal_id]

        if desde:
            clauses.append("cp.fecha >= ?")
            params.append(desde)
        if hasta:
            clauses.append("cp.fecha <= ?")
            params.append(hasta)

        sql = (
            "SELECT cp.id, cp.fecha, t.nombre AS turno, "
            "COALESCE(cp.hora_inicio_override, t.hora_inicio) AS hora_inicio, "
            "COALESCE(cp.hora_fin_override, t.hora_fin) AS hora_fin, "
            "cp.observaciones, cp.activo "
            "FROM calendario_personal cp "
            "JOIN turnos t ON t.id = cp.turno_id "
            "WHERE " + " AND ".join(clauses) + " "
            "ORDER BY cp.fecha"
        )

        rows = self._conn.execute(sql, params).fetchall()
        return [
            CalendarioRow(
                id=row["id"],
                fecha=row["fecha"],
                turno=row["turno"],
                hora_inicio=row["hora_inicio"],
                hora_fin=row["hora_fin"],
                observaciones=row["observaciones"] or "",
                activo=bool(row["activo"]),
            )
            for row in rows
        ]
