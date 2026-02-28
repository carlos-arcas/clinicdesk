# infrastructure/sqlite/repos_recetas.py
"""
Repositorio SQLite para Recetas y Líneas de Receta.

Responsabilidades:
- CRUD de recetas (cabecera) y líneas
- Consultas por paciente, médico y rangos
- Conversión fila <-> modelo de dominio

No contiene:
- Lógica de dispensación
- Validación de stock
- Código de UI
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import List, Optional

from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Receta, RecetaLinea


logger = logging.getLogger(__name__)


class _RecetasConsultasSqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def get_receta_by_id(self, receta_id: int) -> Optional[Receta]:
        row = self._con.execute("SELECT * FROM recetas WHERE id = ?", (receta_id,)).fetchone()
        return self._row_to_receta(row) if row else None

    def list_lineas_by_receta(self, receta_id: int) -> List[RecetaLinea]:
        try:
            rows = self._con.execute(
                """
                SELECT * FROM receta_lineas
                WHERE receta_id = ? AND activo = 1
                ORDER BY id
                """,
                (receta_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en RecetasRepository.list_lineas_by_receta: %s", exc)
            return []
        return [self._row_to_linea(r) for r in rows]

    def list_recetas_by_paciente(
        self,
        paciente_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Receta]:
        if paciente_id <= 0:
            raise ValidationError("paciente_id inválido.")
        return self._list_recetas_filtradas("paciente_id", paciente_id, desde, hasta)

    def list_recetas_by_medico(
        self,
        medico_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Receta]:
        if medico_id <= 0:
            raise ValidationError("medico_id inválido.")
        return self._list_recetas_filtradas("medico_id", medico_id, desde, hasta)

    def _list_recetas_filtradas(
        self,
        filtro_campo: str,
        filtro_valor: int,
        desde: Optional[str],
        hasta: Optional[str],
    ) -> List[Receta]:
        clauses = [f"{filtro_campo} = ?", "activo = 1"]
        params: list[object] = [filtro_valor]
        if desde:
            clauses.append("fecha >= ?")
            params.append(desde)
        if hasta:
            clauses.append("fecha <= ?")
            params.append(hasta)
        sql = "SELECT * FROM recetas WHERE " + " AND ".join(clauses) + " ORDER BY fecha DESC"
        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en RecetasRepository._list_recetas_filtradas: %s", exc)
            return []
        return [self._row_to_receta(r) for r in rows]

    def _row_to_receta(self, row: sqlite3.Row) -> Receta:
        return Receta(
            id=row["id"],
            paciente_id=row["paciente_id"],
            medico_id=row["medico_id"],
            fecha=datetime.fromisoformat(row["fecha"]),
            observaciones=row["observaciones"],
        )

    def _row_to_linea(self, row: sqlite3.Row) -> RecetaLinea:
        return RecetaLinea(
            id=row["id"],
            receta_id=row["receta_id"],
            medicamento_id=row["medicamento_id"],
            dosis=row["dosis"],
            duracion_dias=row["duracion_dias"],
            instrucciones=row["instrucciones"],
        )


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class RecetasRepository:
    """Repositorio de acceso a datos para recetas y receta_lineas."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._consultas = _RecetasConsultasSqlite(connection)

    def create_receta(self, receta: Receta) -> int:
        receta.validar()
        cur = self._con.execute(
            """
            INSERT INTO recetas (
                paciente_id, medico_id, fecha, observaciones
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                receta.paciente_id,
                receta.medico_id,
                receta.fecha.isoformat(sep=" ", timespec="seconds"),
                receta.observaciones,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update_receta(self, receta: Receta) -> None:
        if not receta.id:
            raise ValidationError("No se puede actualizar receta sin id.")
        receta.validar()
        self._con.execute(
            """
            UPDATE recetas SET
                paciente_id = ?,
                medico_id = ?,
                fecha = ?,
                observaciones = ?
            WHERE id = ?
            """,
            (
                receta.paciente_id,
                receta.medico_id,
                receta.fecha.isoformat(sep=" ", timespec="seconds"),
                receta.observaciones,
                receta.id,
            ),
        )
        self._con.commit()

    def get_receta_by_id(self, receta_id: int) -> Optional[Receta]:
        return self._consultas.get_receta_by_id(receta_id)

    def delete_receta(self, receta_id: int) -> None:
        self._con.execute("UPDATE recetas SET activo = 0 WHERE id = ?", (receta_id,))
        self._con.commit()

    def add_linea(self, linea: RecetaLinea) -> int:
        linea.validar()
        cur = self._con.execute(
            """
            INSERT INTO receta_lineas (
                receta_id, medicamento_id, dosis, duracion_dias, instrucciones
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                linea.receta_id,
                linea.medicamento_id,
                linea.dosis,
                linea.duracion_dias,
                linea.instrucciones,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update_linea(self, linea: RecetaLinea) -> None:
        if not linea.id:
            raise ValidationError("No se puede actualizar línea sin id.")
        linea.validar()
        self._con.execute(
            """
            UPDATE receta_lineas SET
                receta_id = ?,
                medicamento_id = ?,
                dosis = ?,
                duracion_dias = ?,
                instrucciones = ?
            WHERE id = ?
            """,
            (
                linea.receta_id,
                linea.medicamento_id,
                linea.dosis,
                linea.duracion_dias,
                linea.instrucciones,
                linea.id,
            ),
        )
        self._con.commit()

    def delete_linea(self, linea_id: int) -> None:
        self._con.execute("UPDATE receta_lineas SET activo = 0 WHERE id = ?", (linea_id,))
        self._con.commit()

    def list_lineas_by_receta(self, receta_id: int) -> List[RecetaLinea]:
        return self._consultas.list_lineas_by_receta(receta_id)

    def list_recetas_by_paciente(
        self,
        paciente_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Receta]:
        return self._consultas.list_recetas_by_paciente(
            paciente_id,
            desde=desde,
            hasta=hasta,
        )

    def list_recetas_by_medico(
        self,
        medico_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Receta]:
        return self._consultas.list_recetas_by_medico(
            medico_id,
            desde=desde,
            hasta=hasta,
        )
