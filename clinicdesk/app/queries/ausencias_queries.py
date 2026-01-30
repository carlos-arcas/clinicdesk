from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AusenciaRow:
    id: int
    inicio: str
    fin: str
    tipo: str
    motivo: str
    aprobado_por: str
    creado_en: str
    persona_id: int
    persona_nombre: str
    persona_tipo: str


class AusenciasQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def list_medico(
        self,
        medico_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[AusenciaRow]:
        clauses = ["a.medico_id = ?"]
        params: List[object] = [medico_id]

        if desde:
            clauses.append("a.fin >= ?")
            params.append(desde)
        if hasta:
            clauses.append("a.inicio <= ?")
            params.append(hasta)

        clauses.append("a.activo = 1")

        sql = (
            "SELECT a.id, a.inicio, a.fin, a.tipo, a.motivo, a.creado_en, "
            "(ap.nombre || ' ' || ap.apellidos) AS aprobado_por, "
            "m.id AS persona_id, (m.nombre || ' ' || m.apellidos) AS persona_nombre "
            "FROM ausencias_medico a "
            "JOIN medicos m ON m.id = a.medico_id "
            "LEFT JOIN personal ap ON ap.id = a.aprobado_por_personal_id "
            "WHERE " + " AND ".join(clauses) + " "
            "ORDER BY a.inicio"
        )

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en AusenciasQueries.list_medico: %s", exc)
            return []
        return [
            AusenciaRow(
                id=row["id"],
                inicio=row["inicio"],
                fin=row["fin"],
                tipo=row["tipo"],
                motivo=row["motivo"] or "",
                aprobado_por=row["aprobado_por"] or "",
                creado_en=row["creado_en"],
                persona_id=row["persona_id"],
                persona_nombre=row["persona_nombre"],
                persona_tipo="medico",
            )
            for row in rows
        ]

    def list_personal(
        self,
        personal_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[AusenciaRow]:
        clauses = ["a.personal_id = ?"]
        params: List[object] = [personal_id]

        if desde:
            clauses.append("a.fin >= ?")
            params.append(desde)
        if hasta:
            clauses.append("a.inicio <= ?")
            params.append(hasta)

        clauses.append("a.activo = 1")

        sql = (
            "SELECT a.id, a.inicio, a.fin, a.tipo, a.motivo, a.creado_en, "
            "(ap.nombre || ' ' || ap.apellidos) AS aprobado_por, "
            "p.id AS persona_id, (p.nombre || ' ' || p.apellidos) AS persona_nombre "
            "FROM ausencias_personal a "
            "JOIN personal p ON p.id = a.personal_id "
            "LEFT JOIN personal ap ON ap.id = a.aprobado_por_personal_id "
            "WHERE " + " AND ".join(clauses) + " "
            "ORDER BY a.inicio"
        )

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en AusenciasQueries.list_personal: %s", exc)
            return []
        return [
            AusenciaRow(
                id=row["id"],
                inicio=row["inicio"],
                fin=row["fin"],
                tipo=row["tipo"],
                motivo=row["motivo"] or "",
                aprobado_por=row["aprobado_por"] or "",
                creado_en=row["creado_en"],
                persona_id=row["persona_id"],
                persona_nombre=row["persona_nombre"],
                persona_tipo="personal",
            )
            for row in rows
        ]
