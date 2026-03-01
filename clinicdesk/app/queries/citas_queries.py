from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import logging

from clinicdesk.app.application.citas.filtros import FiltrosCitasDTO, normalizar_filtros_citas
from clinicdesk.app.application.citas.usecases import PaginacionCitasDTO
from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.container import AppContainer


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CitaRow:
    id: int
    inicio: str
    fin: str
    paciente_id: int
    paciente_nombre: str
    medico_id: int
    medico_nombre: str
    sala_id: int
    sala_nombre: str
    estado: str
    motivo: Optional[str]


@dataclass(frozen=True, slots=True)
class CitaListadoRow:
    id: int
    paciente_id: int
    medico_id: int
    fecha: str
    hora_inicio: str
    hora_fin: str
    paciente: str
    medico: str
    sala: str
    estado: str
    notas_len: int
    tiene_incidencias: bool


_CAMPO_SQL_POR_ATRIBUTO: dict[str, str] = {
    "paciente_id": "c.paciente_id AS paciente_id",
    "medico_id": "c.medico_id AS medico_id",
    "fecha": "date(c.inicio) AS fecha",
    "hora_inicio": "time(c.inicio) AS hora_inicio",
    "hora_fin": "time(c.fin) AS hora_fin",
    "paciente": "(p.nombre || ' ' || p.apellidos) AS paciente",
    "medico": "(m.nombre || ' ' || m.apellidos) AS medico",
    "sala": "s.nombre AS sala",
    "estado": "c.estado AS estado",
    "riesgo": "coalesce(c.riesgo_ausencia, 'NO_DISPONIBLE') AS riesgo",
    "recordatorio": "coalesce(r.estado_global, 'SIN_PREPARAR') AS recordatorio",
    "notas_len": "length(coalesce(c.notas, '')) AS notas_len",
    "incidencias": "CASE WHEN i.cita_id IS NULL THEN 0 ELSE 1 END AS tiene_incidencias",
}


class CitasQueries:
    """Consultas de lectura para Citas (UI/auditoría)."""

    def __init__(self, container: AppContainer) -> None:
        self._c = container

    def buscar_para_lista(
        self,
        filtros_norm: FiltrosCitasDTO,
        paginacion: PaginacionCitasDTO,
        columnas: tuple[str, ...],
    ) -> tuple[list[dict[str, object]], int]:
        where_sql, params = self._build_common_filters(filtros_norm)
        campos = _resolver_select_fields(columnas)
        sql = _sql_lista(where_sql, campos)
        rows = self._c.connection.execute(sql, (*params, paginacion.limit, paginacion.offset)).fetchall()
        total = int(self._c.connection.execute(_sql_count(where_sql), params).fetchone()["total"])
        return ([dict(row) for row in rows], total)

    def buscar_para_calendario(
        self,
        filtros_norm: FiltrosCitasDTO,
        columnas: tuple[str, ...],
    ) -> list[dict[str, object]]:
        where_sql, params = self._build_common_filters(filtros_norm)
        campos = _resolver_select_fields(columnas)
        sql = _sql_calendario(where_sql, campos)
        rows = self._c.connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def list_by_date(self, yyyy_mm_dd: str) -> list[CitaRow]:
        yyyy_mm_dd = normalize_search_text(yyyy_mm_dd)
        if not yyyy_mm_dd:
            logger.info("citas_list_by_date_skip", extra={"reason_code": "fecha_vacia"})
            return []
        try:
            rows = self._c.connection.execute(_sql_by_date(), (f"{yyyy_mm_dd}%",)).fetchall()
        except Exception as exc:  # noqa: BLE001
            logger.error("citas_list_by_date_sql_error", extra={"reason_code": "sql_error", "error": str(exc)})
            return []
        return [_map_cita_row(r) for r in rows]

    def search_listado(self, *, desde: str, hasta: str, texto: str, estado: str) -> list[CitaListadoRow]:
        if not desde or not hasta or desde > hasta:
            logger.info("citas_search_listado_skip", extra={"reason_code": "rango_invalido"})
            return []

        filtros = normalizar_filtros_citas(
            FiltrosCitasDTO(
                rango_preset="PERSONALIZADO",
                desde=datetime.fromisoformat(f"{desde}T00:00:00"),
                hasta=datetime.fromisoformat(f"{hasta}T23:59:59"),
                texto_busqueda=texto,
                estado=estado,
            ),
            datetime.now(),
        )
        columnas = (
            "paciente_id",
            "medico_id",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "paciente",
            "medico",
            "sala",
            "estado",
            "notas_len",
            "incidencias",
        )
        rows, _ = self.buscar_para_lista(filtros, PaginacionCitasDTO(limit=10000, offset=0), columnas)
        return [_map_listado_row(row) for row in rows]

    def _build_common_filters(self, filtros: FiltrosCitasDTO) -> tuple[str, tuple[object, ...]]:
        if filtros.desde is None or filtros.hasta is None:
            raise ValueError("Los filtros de citas deben llegar normalizados con rango cerrado.")

        clauses = ["c.activo = 1", "datetime(c.inicio) >= datetime(?)", "datetime(c.inicio) <= datetime(?)"]
        params: list[object] = [filtros.desde.isoformat(sep=" "), filtros.hasta.isoformat(sep=" ")]

        if filtros.estado:
            clauses.append("c.estado = ?")
            params.append(filtros.estado)
        if filtros.medico_id:
            clauses.append("c.medico_id = ?")
            params.append(filtros.medico_id)
        if filtros.sala_id:
            clauses.append("c.sala_id = ?")
            params.append(filtros.sala_id)
        if filtros.paciente_id:
            clauses.append("c.paciente_id = ?")
            params.append(filtros.paciente_id)
        if filtros.texto_busqueda:
            like = f"%{filtros.texto_busqueda.lower()}%"
            clauses.append(_sql_text_search())
            params.extend([like, like, like, like, like])
        if filtros.recordatorio_filtro == "SIN_PREPARAR":
            clauses.append("coalesce(r.estado_global, 'SIN_PREPARAR') = 'SIN_PREPARAR'")
        if filtros.recordatorio_filtro == "NO_ENVIADO":
            clauses.append("coalesce(r.estado_global, 'SIN_PREPARAR') != 'ENVIADO'")

        return " AND ".join(clauses), tuple(params)


def _resolver_select_fields(columnas: tuple[str, ...]) -> tuple[str, ...]:
    campos = ["c.id AS cita_id"]
    for columna in columnas:
        campo = _CAMPO_SQL_POR_ATRIBUTO.get(columna)
        if campo and campo not in campos:
            campos.append(campo)
    return tuple(campos)


def _sql_by_date() -> str:
    return """
        SELECT c.id, c.inicio, c.fin, c.paciente_id,
               (p.nombre || ' ' || p.apellidos) AS paciente_nombre,
               c.medico_id, (m.nombre || ' ' || m.apellidos) AS medico_nombre,
               c.sala_id, s.nombre AS sala_nombre, c.estado, c.motivo
        FROM citas c
        JOIN pacientes p ON p.id = c.paciente_id
        JOIN medicos m ON m.id = c.medico_id
        JOIN salas s ON s.id = c.sala_id
        WHERE c.inicio LIKE ? AND c.activo = 1
        ORDER BY c.inicio
    """


def _sql_text_search() -> str:
    return (
        "(lower(c.motivo) LIKE ? OR lower(c.notas) LIKE ? OR "
        "lower(p.nombre || ' ' || p.apellidos) LIKE ? OR "
        "lower(m.nombre || ' ' || m.apellidos) LIKE ? OR lower(s.nombre) LIKE ?)"
    )


def _sql_calendario(where_sql: str, campos: tuple[str, ...]) -> str:
    return (
        "WITH recordatorios_agg AS ("
        "SELECT cita_id, CASE "
        "WHEN max(CASE WHEN estado = 'ENVIADO' THEN 1 ELSE 0 END) = 1 THEN 'ENVIADO' "
        "WHEN max(CASE WHEN estado = 'PREPARADO' THEN 1 ELSE 0 END) = 1 THEN 'PREPARADO' "
        "ELSE 'SIN_PREPARAR' END AS estado_global FROM recordatorios_citas GROUP BY cita_id"
        "), incidencias_agg AS (SELECT DISTINCT cita_id FROM incidencias WHERE activo = 1) "
        f"SELECT {', '.join(campos)} FROM citas c "
        "JOIN pacientes p ON p.id = c.paciente_id "
        "JOIN medicos m ON m.id = c.medico_id "
        "JOIN salas s ON s.id = c.sala_id "
        "LEFT JOIN recordatorios_agg r ON r.cita_id = c.id "
        "LEFT JOIN incidencias_agg i ON i.cita_id = c.id "
        f"WHERE {where_sql} ORDER BY c.inicio"
    )


def _sql_lista(where_sql: str, campos: tuple[str, ...]) -> str:
    return _sql_calendario(where_sql, campos) + " LIMIT ? OFFSET ?"


def _sql_count(where_sql: str) -> str:
    return (
        "WITH recordatorios_agg AS ("
        "SELECT cita_id, CASE "
        "WHEN max(CASE WHEN estado = 'ENVIADO' THEN 1 ELSE 0 END) = 1 THEN 'ENVIADO' "
        "WHEN max(CASE WHEN estado = 'PREPARADO' THEN 1 ELSE 0 END) = 1 THEN 'PREPARADO' "
        "ELSE 'SIN_PREPARAR' END AS estado_global FROM recordatorios_citas GROUP BY cita_id"
        ") SELECT count(1) AS total FROM citas c "
        "JOIN pacientes p ON p.id = c.paciente_id "
        "JOIN medicos m ON m.id = c.medico_id "
        "JOIN salas s ON s.id = c.sala_id "
        "LEFT JOIN recordatorios_agg r ON r.cita_id = c.id "
        f"WHERE {where_sql}"
    )


def _map_cita_row(row) -> CitaRow:
    return CitaRow(
        id=int(row["id"]),
        inicio=row["inicio"],
        fin=row["fin"],
        paciente_id=int(row["paciente_id"]),
        paciente_nombre=row["paciente_nombre"],
        medico_id=int(row["medico_id"]),
        medico_nombre=row["medico_nombre"],
        sala_id=int(row["sala_id"]),
        sala_nombre=row["sala_nombre"],
        estado=row["estado"],
        motivo=row["motivo"],
    )


def _map_listado_row(row: dict[str, object]) -> CitaListadoRow:
    return CitaListadoRow(
        id=int(row["cita_id"]),
        paciente_id=int(row.get("paciente_id", 0)),
        medico_id=int(row.get("medico_id", 0)),
        fecha=str(row.get("fecha", "")),
        hora_inicio=str(row.get("hora_inicio", "")),
        hora_fin=str(row.get("hora_fin", "")),
        paciente=str(row.get("paciente", "")),
        medico=str(row.get("medico", "")),
        sala=str(row.get("sala", "")),
        estado=str(row.get("estado", "")),
        notas_len=int(row.get("notas_len", 0)),
        tiene_incidencias=bool(row.get("tiene_incidencias", 0)),
    )
