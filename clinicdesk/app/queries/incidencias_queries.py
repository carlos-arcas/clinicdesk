from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sqlite3


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


class IncidenciasQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def list(
        self,
        *,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        severidad: Optional[str] = None,
        fecha_desde: Optional[str] = None,  # YYYY-MM-DD
        fecha_hasta: Optional[str] = None,  # YYYY-MM-DD
        texto: Optional[str] = None,
        limit: int = 500,
    ) -> List[IncidenciaRow]:
        where = []
        params: List[object] = []

        if tipo:
            where.append("i.tipo = ?")
            params.append(tipo)
        if estado:
            where.append("i.estado = ?")
            params.append(estado)
        if severidad:
            where.append("i.severidad = ?")
            params.append(severidad)
        if fecha_desde:
            where.append("i.fecha_hora >= ?")
            params.append(f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            where.append("i.fecha_hora <= ?")
            params.append(f"{fecha_hasta} 23:59:59")
        if texto:
            like = f"%{texto}%"
            where.append(
                "(i.descripcion LIKE ? OR i.nota_override LIKE ? OR cp.nombre LIKE ? OR cp.apellidos LIKE ?)"
            )
            params.extend([like, like, like, like])

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

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
            (*params, int(limit)),
        ).fetchall()

        out: List[IncidenciaRow] = []
        for r in rows:
            out.append(
                IncidenciaRow(
                    id=int(r["id"]),
                    tipo=r["tipo"],
                    severidad=r["severidad"],
                    estado=r["estado"],
                    fecha_hora=r["fecha_hora"],
                    descripcion=r["descripcion"],
                    nota_override=r["nota_override"],
                    confirmado_por_personal_id=int(r["confirmado_por_personal_id"]),
                    confirmado_por_nombre=r["confirmado_por_nombre"],
                    medico_id=r["medico_id"],
                    medico_nombre=r["medico_nombre"],
                    personal_id=r["personal_id"],
                    personal_nombre=r["personal_nombre"],
                    cita_id=r["cita_id"],
                    receta_id=r["receta_id"],
                    dispensacion_id=r["dispensacion_id"],
                )
            )
        return out

    def get_by_id(self, incidencia_id: int) -> Optional[IncidenciaRow]:
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
            WHERE i.id = ?
            """,
            (incidencia_id,),
        ).fetchone()

        if not row:
            return None

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
