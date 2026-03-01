from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

import logging

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
    notas_len: int


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


class CitasQueries:
    """Consultas de lectura para Citas (UI/auditoría)."""

    _MAX_DIAS_RANGO_LISTADO = 93

    def __init__(self, container: AppContainer) -> None:
        self._c = container

    def list_by_date(self, yyyy_mm_dd: str) -> List[CitaRow]:
        yyyy_mm_dd = normalize_search_text(yyyy_mm_dd)
        if not yyyy_mm_dd:
            logger.info("Citas list_by_date skipped (fecha vacía).")
            return []
        try:
            rows = self._c.connection.execute(self._sql_by_date(), (f"{yyyy_mm_dd}%",)).fetchall()
        except Exception as exc:
            logger.error("Error SQL en CitasQueries.list_by_date: %s", exc)
            return []
        return [self._map_cita_row(r) for r in rows]

    def search_listado(
        self,
        *,
        desde: str,
        hasta: str,
        texto: str,
        estado: str,
    ) -> List[CitaListadoRow]:
        texto_norm = normalize_search_text(texto)
        estado_norm = normalize_search_text(estado).upper()
        if not self._rango_listado_permitido(desde, hasta):
            logger.info("Citas search_listado skipped (rango inválido).")
            return []
        like = f"%{texto_norm}%" if texto_norm else ""
        params = self._params_listado(desde, hasta, estado_norm, texto_norm, like)
        logger.info(
            "citas_search_listado",
            extra={
                "desde": desde,
                "hasta": hasta,
                "estado": estado_norm or "TODOS",
                "texto_busqueda": self._texto_busqueda_redactado(texto_norm),
            },
        )

        try:
            rows = self._c.connection.execute(self._sql_listado(), params).fetchall()
        except Exception as exc:
            logger.error("Error SQL en CitasQueries.search_listado: %s", exc)
            return []
        return [self._map_listado_row(row) for row in rows]

    def _rango_listado_permitido(self, desde: str, hasta: str) -> bool:
        if not desde or not hasta:
            return False
        try:
            fecha_desde = date.fromisoformat(desde)
            fecha_hasta = date.fromisoformat(hasta)
        except ValueError:
            return False
        if fecha_desde > fecha_hasta:
            return False
        return (fecha_hasta - fecha_desde).days <= self._MAX_DIAS_RANGO_LISTADO

    @staticmethod
    def _params_listado(desde: str, hasta: str, estado: str, texto: str, like: str) -> tuple[object, ...]:
        estado_filtrado = estado or "TODOS"
        texto_filtrado = texto or ""
        return (
            desde,
            hasta,
            estado_filtrado,
            estado_filtrado,
            texto_filtrado,
            like,
            like,
            like,
            like,
            like,
        )

    @staticmethod
    def _texto_busqueda_redactado(texto: str) -> str:
        if not texto:
            return ""
        if len(texto) <= 3:
            return "***"
        return f"{texto[:3]}***({len(texto)})"

    @staticmethod
    def _sql_by_date() -> str:
        return """
            SELECT
                c.id,
                c.inicio,
                c.fin,
                c.paciente_id,
                (p.nombre || ' ' || p.apellidos) AS paciente_nombre,
                c.medico_id,
                (m.nombre || ' ' || m.apellidos) AS medico_nombre,
                c.sala_id,
                s.nombre AS sala_nombre,
                c.estado,
                c.motivo,
                length(coalesce(c.notas, '')) AS notas_len
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            JOIN salas s ON s.id = c.sala_id
            WHERE c.inicio LIKE ? AND c.activo = 1
            ORDER BY c.inicio
        """


    @staticmethod
    def _sql_listado() -> str:
        return (
            "SELECT c.id, "
            "c.paciente_id, "
            "c.medico_id, "
            "date(c.inicio) AS fecha, "
            "time(c.inicio) AS hora_inicio, "
            "time(c.fin) AS hora_fin, "
            "(p.nombre || ' ' || p.apellidos) AS paciente, "
            "(m.nombre || ' ' || m.apellidos) AS medico, "
            "s.nombre AS sala, "
            "c.estado, "
            "length(coalesce(c.notas, '')) AS notas_len, "
            "CASE WHEN EXISTS ("
            "SELECT 1 FROM incidencias i WHERE i.cita_id = c.id AND i.activo = 1"
            ") THEN 1 ELSE 0 END AS tiene_incidencias "
            "FROM citas c "
            "JOIN pacientes p ON p.id = c.paciente_id "
            "JOIN medicos m ON m.id = c.medico_id "
            "JOIN salas s ON s.id = c.sala_id "
            "WHERE c.activo = 1 "
            "AND date(c.inicio) >= date(?) "
            "AND date(c.inicio) <= date(?) "
            "AND (? = 'TODOS' OR c.estado = ?) "
            "AND (? = '' OR "
            "(lower(c.motivo) LIKE ? OR "
            "lower(c.notas) LIKE ? OR "
            "lower(p.nombre || ' ' || p.apellidos) LIKE ? OR "
            "lower(m.nombre || ' ' || m.apellidos) LIKE ? OR "
            "lower(s.nombre) LIKE ?)) "
            "ORDER BY c.inicio"
        )

    @staticmethod
    def _map_cita_row(r) -> CitaRow:
        return CitaRow(
            id=int(r["id"]),
            inicio=r["inicio"],
            fin=r["fin"],
            paciente_id=int(r["paciente_id"]),
            paciente_nombre=r["paciente_nombre"],
            medico_id=int(r["medico_id"]),
            medico_nombre=r["medico_nombre"],
            sala_id=int(r["sala_id"]),
            sala_nombre=r["sala_nombre"],
            estado=r["estado"],
            motivo=r["motivo"],
            notas_len=int(r["notas_len"]),
        )

    @staticmethod
    def _map_listado_row(row) -> CitaListadoRow:
        return CitaListadoRow(
            id=int(row["id"]),
            paciente_id=int(row["paciente_id"]),
            medico_id=int(row["medico_id"]),
            fecha=row["fecha"],
            hora_inicio=row["hora_inicio"],
            hora_fin=row["hora_fin"],
            paciente=row["paciente"],
            medico=row["medico"],
            sala=row["sala"],
            estado=row["estado"],
            notas_len=int(row["notas_len"]),
            tiene_incidencias=bool(row["tiene_incidencias"]),
        )
