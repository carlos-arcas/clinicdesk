from __future__ import annotations

from dataclasses import dataclass
import sqlite3


@dataclass(frozen=True, slots=True)
class FiltrosConfirmacionesQuery:
    desde: str
    hasta: str
    texto_paciente: str = ""
    recordatorio_filtro: str = "TODOS"


@dataclass(frozen=True, slots=True)
class CitaConfirmacionRow:
    cita_id: int
    inicio: str
    paciente_nombre: str
    medico_nombre: str
    estado_cita: str
    paciente_id: int
    medico_id: int
    recordatorio_estado_global: str


class ConfirmacionesQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def buscar_citas_confirmaciones(
        self,
        filtros: FiltrosConfirmacionesQuery,
        limit: int,
        offset: int,
    ) -> tuple[list[CitaConfirmacionRow], int]:
        where_sql, params = self._build_filters(filtros)
        rows = self._con.execute(
            self._sql_busqueda(where_sql),
            (*params, limit, offset),
        ).fetchall()
        total_row = self._con.execute(self._sql_total(where_sql), params).fetchone()
        total = int(total_row["total"]) if total_row else 0
        return ([self._map_row(row) for row in rows], total)

    def _build_filters(self, filtros: FiltrosConfirmacionesQuery) -> tuple[str, tuple[object, ...]]:
        clauses = ["c.activo = 1", "date(c.inicio) >= date(?)", "date(c.inicio) <= date(?)"]
        params: list[object] = [filtros.desde, filtros.hasta]
        texto = filtros.texto_paciente.strip().lower()
        if texto:
            clauses.append("lower(p.nombre || ' ' || p.apellidos) LIKE ?")
            params.append(f"%{texto}%")
        recordatorio = filtros.recordatorio_filtro.upper().strip()
        if recordatorio == "SIN_PREPARAR":
            clauses.append("coalesce(r.estado_global, 'SIN_PREPARAR') = 'SIN_PREPARAR'")
        if recordatorio == "NO_ENVIADO":
            clauses.append("coalesce(r.estado_global, 'SIN_PREPARAR') != 'ENVIADO'")
        return (" AND ".join(clauses), tuple(params))

    @staticmethod
    def _sql_busqueda(where_sql: str) -> str:
        return (
            "WITH recordatorios_agg AS ("
            "SELECT cita_id, "
            "CASE "
            "WHEN max(CASE WHEN estado = 'ENVIADO' THEN 1 ELSE 0 END) = 1 THEN 'ENVIADO' "
            "WHEN max(CASE WHEN estado = 'PREPARADO' THEN 1 ELSE 0 END) = 1 THEN 'PREPARADO' "
            "ELSE 'SIN_PREPARAR' END AS estado_global "
            "FROM recordatorios_citas GROUP BY cita_id"
            ") "
            "SELECT c.id AS cita_id, c.inicio, "
            "p.nombre || ' ' || p.apellidos AS paciente_nombre, "
            "m.nombre || ' ' || m.apellidos AS medico_nombre, "
            "c.estado AS estado_cita, c.paciente_id, c.medico_id, "
            "coalesce(r.estado_global, 'SIN_PREPARAR') AS recordatorio_estado_global "
            "FROM citas c "
            "JOIN pacientes p ON p.id = c.paciente_id "
            "JOIN medicos m ON m.id = c.medico_id "
            "LEFT JOIN recordatorios_agg r ON r.cita_id = c.id "
            f"WHERE {where_sql} "
            "ORDER BY c.inicio ASC LIMIT ? OFFSET ?"
        )

    @staticmethod
    def _sql_total(where_sql: str) -> str:
        return (
            "WITH recordatorios_agg AS ("
            "SELECT cita_id, "
            "CASE "
            "WHEN max(CASE WHEN estado = 'ENVIADO' THEN 1 ELSE 0 END) = 1 THEN 'ENVIADO' "
            "WHEN max(CASE WHEN estado = 'PREPARADO' THEN 1 ELSE 0 END) = 1 THEN 'PREPARADO' "
            "ELSE 'SIN_PREPARAR' END AS estado_global "
            "FROM recordatorios_citas GROUP BY cita_id"
            ") "
            "SELECT count(1) AS total "
            "FROM citas c "
            "JOIN pacientes p ON p.id = c.paciente_id "
            "LEFT JOIN recordatorios_agg r ON r.cita_id = c.id "
            f"WHERE {where_sql}"
        )

    @staticmethod
    def _map_row(row: sqlite3.Row) -> CitaConfirmacionRow:
        return CitaConfirmacionRow(
            cita_id=int(row["cita_id"]),
            inicio=str(row["inicio"]),
            paciente_nombre=str(row["paciente_nombre"]),
            medico_nombre=str(row["medico_nombre"]),
            estado_cita=str(row["estado_cita"]),
            paciente_id=int(row["paciente_id"]),
            medico_id=int(row["medico_id"]),
            recordatorio_estado_global=str(row["recordatorio_estado_global"]),
        )
