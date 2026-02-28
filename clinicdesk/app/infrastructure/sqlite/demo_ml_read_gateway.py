from __future__ import annotations

import sqlite3
from typing import Any

from clinicdesk.app.common.search_utils import like_value, normalize_search_text


class SqliteDemoMLReadGateway:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def list_doctors(self, query: str | None, limit: int) -> list[dict[str, Any]]:
        where, params = self._build_people_filter(query)
        rows = self._con.execute(
            f"""
            SELECT id, documento, nombre, apellidos, telefono, especialidad, activo
            FROM medicos
            {where}
            ORDER BY apellidos, nombre
            LIMIT ?
            """,
            (*params, int(limit)),
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "documento": row["documento"],
                "nombre_completo": f"{row['nombre']} {row['apellidos']}".strip(),
                "telefono": row["telefono"] or "",
                "especialidad": row["especialidad"] or "",
                "activo": bool(row["activo"]),
            }
            for row in rows
        ]

    def list_patients(self, query: str | None, limit: int) -> list[dict[str, Any]]:
        where, params = self._build_people_filter(query)
        rows = self._con.execute(
            f"""
            SELECT id, documento, nombre, apellidos, telefono, activo
            FROM pacientes
            {where}
            ORDER BY apellidos, nombre
            LIMIT ?
            """,
            (*params, int(limit)),
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "documento": row["documento"],
                "nombre_completo": f"{row['nombre']} {row['apellidos']}".strip(),
                "telefono": row["telefono"] or "",
                "activo": bool(row["activo"]),
            }
            for row in rows
        ]

    def list_appointments(
        self,
        query: str | None,
        from_date: str | None,
        to_date: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        where = ["c.activo = 1"]
        params: list[Any] = []
        text = normalize_search_text(query)
        if text:
            like = like_value(text)
            where.append(
                "((p.nombre || ' ' || p.apellidos) LIKE ? COLLATE NOCASE OR "
                "(m.nombre || ' ' || m.apellidos) LIKE ? COLLATE NOCASE OR c.estado LIKE ? COLLATE NOCASE)"
            )
            params.extend([like, like, like])
        if from_date:
            where.append("c.inicio >= ?")
            params.append(f"{from_date} 00:00:00")
        if to_date:
            where.append("c.inicio <= ?")
            params.append(f"{to_date} 23:59:59")
        where_sql = "WHERE " + " AND ".join(where)
        rows = self._con.execute(
            f"""
            SELECT c.id, c.inicio, c.fin, c.estado, c.motivo,
                   (p.nombre || ' ' || p.apellidos) AS paciente_nombre,
                   (m.nombre || ' ' || m.apellidos) AS medico_nombre
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            {where_sql}
            ORDER BY c.inicio DESC, c.id DESC
            LIMIT ?
            """,
            (*params, int(limit)),
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "inicio": row["inicio"],
                "fin": row["fin"],
                "paciente_nombre": row["paciente_nombre"],
                "medico_nombre": row["medico_nombre"],
                "estado": row["estado"],
                "motivo": row["motivo"] or "",
            }
            for row in rows
        ]

    def list_incidences(self, query: str | None, limit: int) -> list[dict[str, Any]]:
        where = ["activo = 1"]
        params: list[Any] = []
        text = normalize_search_text(query)
        if text:
            where.append("(descripcion LIKE ? COLLATE NOCASE OR estado LIKE ? COLLATE NOCASE)")
            like = like_value(text)
            params.extend([like, like])
        where_sql = "WHERE " + " AND ".join(where)
        rows = self._con.execute(
            f"""
            SELECT id, fecha_hora, tipo, severidad, estado, descripcion
            FROM incidencias
            {where_sql}
            ORDER BY fecha_hora DESC, id DESC
            LIMIT ?
            """,
            (*params, int(limit)),
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "fecha_hora": row["fecha_hora"],
                "tipo": row["tipo"],
                "severidad": row["severidad"],
                "estado": row["estado"],
                "descripcion": row["descripcion"],
            }
            for row in rows
        ]

    def _build_people_filter(self, query: str | None) -> tuple[str, list[Any]]:
        text = normalize_search_text(query)
        if not text:
            return "", []
        like = like_value(text)
        where = "WHERE (nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE OR documento LIKE ? COLLATE NOCASE)"
        return where, [like, like, like]
