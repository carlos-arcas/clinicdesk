# infrastructure/sqlite/repos_incidencias.py
"""
Repositorio SQLite para Incidencias.

Responsabilidades:
- CRUD de incidencias
- Consultas por fecha, tipo, estado y entidades relacionadas
- Soporte para auditoría (incidencias confirmadas con nota_override)

No contiene:
- Lógica de detección de incidencias (eso va en casos de uso)
- Código de UI
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.domain.exceptions import ValidationError


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Modelo ligero de incidencia
# ---------------------------------------------------------------------


@dataclass(slots=True)
class Incidencia:
    """
    Registro de incidencia (auditoría).

    nota_override:
    - Texto obligatorio cuando se confirma/guarda una acción a pesar de advertencia.
    """

    id: Optional[int] = None

    tipo: str = ""         # ej: "CALENDARIO", "CITA", "DISPENSACION", "STOCK"
    severidad: str = ""    # ej: "BAJA", "MEDIA", "ALTA"
    estado: str = ""       # ej: "ABIERTA", "EN_REVISION", "CERRADA"

    fecha_hora: str = ""   # ISO datetime "YYYY-MM-DD HH:MM:SS"
    descripcion: str = ""

    medico_id: Optional[int] = None
    personal_id: Optional[int] = None

    cita_id: Optional[int] = None
    dispensacion_id: Optional[int] = None
    receta_id: Optional[int] = None

    confirmado_por_personal_id: int = 0
    nota_override: str = ""

    def validar(self) -> None:
        if not self.tipo.strip():
            raise ValidationError("tipo de incidencia obligatorio.")
        if not self.severidad.strip():
            raise ValidationError("severidad obligatoria.")
        if not self.estado.strip():
            raise ValidationError("estado obligatorio.")
        if not self.fecha_hora:
            raise ValidationError("fecha_hora obligatoria.")
        if not self.descripcion.strip():
            raise ValidationError("descripcion obligatoria.")
        if self.confirmado_por_personal_id <= 0:
            raise ValidationError("confirmado_por_personal_id inválido.")
        if not self.nota_override.strip():
            raise ValidationError("nota_override obligatoria.")


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class IncidenciasRepository:
    """
    Repositorio de acceso a datos para incidencias.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, incidencia: Incidencia) -> int:
        """
        Inserta una incidencia y devuelve su id.
        """
        incidencia.validar()

        cur = self._con.execute(
            """
            INSERT INTO incidencias (
                tipo, severidad, estado,
                fecha_hora, descripcion,
                medico_id, personal_id,
                cita_id, dispensacion_id, receta_id,
                confirmado_por_personal_id, nota_override
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incidencia.tipo,
                incidencia.severidad,
                incidencia.estado,
                incidencia.fecha_hora,
                incidencia.descripcion,
                incidencia.medico_id,
                incidencia.personal_id,
                incidencia.cita_id,
                incidencia.dispensacion_id,
                incidencia.receta_id,
                incidencia.confirmado_por_personal_id,
                incidencia.nota_override,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, incidencia: Incidencia) -> None:
        """
        Actualiza una incidencia existente.
        """
        if not incidencia.id:
            raise ValidationError("No se puede actualizar una incidencia sin id.")

        incidencia.validar()

        self._con.execute(
            """
            UPDATE incidencias SET
                tipo = ?,
                severidad = ?,
                estado = ?,
                fecha_hora = ?,
                descripcion = ?,
                medico_id = ?,
                personal_id = ?,
                cita_id = ?,
                dispensacion_id = ?,
                receta_id = ?,
                confirmado_por_personal_id = ?,
                nota_override = ?
            WHERE id = ?
            """,
            (
                incidencia.tipo,
                incidencia.severidad,
                incidencia.estado,
                incidencia.fecha_hora,
                incidencia.descripcion,
                incidencia.medico_id,
                incidencia.personal_id,
                incidencia.cita_id,
                incidencia.dispensacion_id,
                incidencia.receta_id,
                incidencia.confirmado_por_personal_id,
                incidencia.nota_override,
                incidencia.id,
            ),
        )
        self._con.commit()

    def update_state(self, incidencia_id: int, estado: str) -> None:
        """
        Actualiza únicamente el estado de una incidencia.
        """
        if incidencia_id <= 0:
            raise ValidationError("incidencia_id inválido.")
        if not estado.strip():
            raise ValidationError("estado obligatorio.")

        self._con.execute(
            "UPDATE incidencias SET estado = ? WHERE id = ?",
            (estado, incidencia_id),
        )
        self._con.commit()

    def delete(self, incidencia_id: int) -> None:
        """
        Borrado lógico: marca la incidencia como inactiva.
        """
        self._con.execute("UPDATE incidencias SET activo = 0 WHERE id = ?", (incidencia_id,))
        self._con.commit()

    def get_by_id(self, incidencia_id: int) -> Optional[Incidencia]:
        """
        Obtiene una incidencia por id.
        """
        row = self._con.execute(
            "SELECT * FROM incidencias WHERE id = ?",
            (incidencia_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    # --------------------------------------------------------------
    # Consultas
    # --------------------------------------------------------------

    def search(
        self,
        *,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        severidad: Optional[str] = None,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
        medico_id: Optional[int] = None,
        personal_id: Optional[int] = None,
        cita_id: Optional[int] = None,
        dispensacion_id: Optional[int] = None,
        receta_id: Optional[int] = None,
    ) -> List[Incidencia]:
        """
        Búsqueda flexible de incidencias para auditoría.
        """
        clauses, params = _build_search_query(
            tipo=tipo,
            estado=estado,
            severidad=severidad,
            desde=desde,
            hasta=hasta,
            medico_id=medico_id,
            personal_id=personal_id,
            cita_id=cita_id,
            dispensacion_id=dispensacion_id,
            receta_id=receta_id,
        )
        sql = "SELECT * FROM incidencias"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY fecha_hora DESC"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en IncidenciasRepository.search: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def list_open(self) -> List[Incidencia]:
        """
        Lista incidencias abiertas (estado = 'ABIERTA').
        """
        try:
            rows = self._con.execute(
                """
                SELECT * FROM incidencias
                WHERE estado = 'ABIERTA' AND activo = 1
                ORDER BY fecha_hora DESC
                """
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en IncidenciasRepository.list_open: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Incidencia:
        """
        Convierte fila SQLite en Incidencia.
        """
        return Incidencia(
            id=row["id"],
            tipo=row["tipo"],
            severidad=row["severidad"],
            estado=row["estado"],
            fecha_hora=row["fecha_hora"],
            descripcion=row["descripcion"],
            medico_id=row["medico_id"],
            personal_id=row["personal_id"],
            cita_id=row["cita_id"],
            dispensacion_id=row["dispensacion_id"],
            receta_id=row["receta_id"],
            confirmado_por_personal_id=row["confirmado_por_personal_id"],
            nota_override=row["nota_override"],
        )


def _build_search_query(
    *,
    tipo: Optional[str],
    estado: Optional[str],
    severidad: Optional[str],
    desde: Optional[str],
    hasta: Optional[str],
    medico_id: Optional[int],
    personal_id: Optional[int],
    cita_id: Optional[int],
    dispensacion_id: Optional[int],
    receta_id: Optional[int],
) -> tuple[list[str], list[str | int]]:
    tipo = normalize_search_text(tipo)
    estado = normalize_search_text(estado)
    severidad = normalize_search_text(severidad)
    desde = normalize_search_text(desde)
    hasta = normalize_search_text(hasta)
    clauses: list[str] = ["activo = 1"]
    params: list[str | int] = []

    _append_like_clause(clauses, params, "tipo", tipo)
    _append_like_clause(clauses, params, "estado", estado)
    _append_like_clause(clauses, params, "severidad", severidad)
    _append_range_clause(clauses, params, "fecha_hora >= ?", desde)
    _append_range_clause(clauses, params, "fecha_hora <= ?", hasta)

    _append_optional_id_clause(clauses, params, "medico_id", medico_id)
    _append_optional_id_clause(clauses, params, "personal_id", personal_id)
    _append_optional_id_clause(clauses, params, "cita_id", cita_id)
    _append_optional_id_clause(clauses, params, "dispensacion_id", dispensacion_id)
    _append_optional_id_clause(clauses, params, "receta_id", receta_id)
    return clauses, params


def _append_like_clause(clauses: list[str], params: list[str | int], field: str, value: Optional[str]) -> None:
    if not value:
        return
    clauses.append(f"{field} LIKE ? COLLATE NOCASE")
    params.append(like_value(value))


def _append_range_clause(clauses: list[str], params: list[str | int], clause: str, value: Optional[str]) -> None:
    if not value:
        return
    clauses.append(clause)
    params.append(value)


def _append_optional_id_clause(
    clauses: list[str],
    params: list[str | int],
    field: str,
    value: Optional[int],
) -> None:
    if value is None:
        return
    clauses.append(f"{field} = ?")
    params.append(value)
