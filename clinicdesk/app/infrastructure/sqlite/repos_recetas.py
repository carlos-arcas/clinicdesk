"""Repositorio SQLite para recetas y líneas de receta."""

from __future__ import annotations

import logging
import sqlite3
from typing import Optional

from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Receta, RecetaLinea
from clinicdesk.app.infrastructure.sqlite.recetas.consultas import construir_consulta_por_actor
from clinicdesk.app.infrastructure.sqlite.recetas.mapping import row_to_linea, row_to_receta
from clinicdesk.app.infrastructure.sqlite.recetas.sql import (
    INSERT_LINEA,
    INSERT_RECETA,
    SELECT_LINEAS_ACTIVAS,
    UPDATE_LINEA,
    UPDATE_RECETA,
)

logger = logging.getLogger(__name__)


class RecetasRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def create_receta(self, receta: Receta) -> int:
        receta.validar()
        cur = self._con.execute(
            INSERT_RECETA,
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
            UPDATE_RECETA,
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
        row = self._con.execute("SELECT * FROM recetas WHERE id = ?", (receta_id,)).fetchone()
        return row_to_receta(row) if row else None

    def delete_receta(self, receta_id: int) -> None:
        self._con.execute("UPDATE recetas SET activo = 0 WHERE id = ?", (receta_id,))
        self._con.commit()

    def add_linea(self, linea: RecetaLinea) -> int:
        linea.validar()
        cur = self._con.execute(
            INSERT_LINEA,
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
            UPDATE_LINEA,
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

    def list_lineas_by_receta(self, receta_id: int) -> list[RecetaLinea]:
        try:
            rows = self._con.execute(SELECT_LINEAS_ACTIVAS, (receta_id,)).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en RecetasRepository.list_lineas_by_receta: %s", exc)
            return []
        return [row_to_linea(row) for row in rows]

    def list_recetas_by_paciente(
        self,
        paciente_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> list[Receta]:
        sql, params = construir_consulta_por_actor(
            campo_actor="paciente",
            actor_id=paciente_id,
            desde=desde,
            hasta=hasta,
        )
        return self._listar_recetas(sql, params, contexto="list_recetas_by_paciente")

    def list_recetas_by_medico(
        self,
        medico_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> list[Receta]:
        sql, params = construir_consulta_por_actor(
            campo_actor="medico",
            actor_id=medico_id,
            desde=desde,
            hasta=hasta,
        )
        return self._listar_recetas(sql, params, contexto="list_recetas_by_medico")

    def _listar_recetas(self, sql: str, params: list[object], *, contexto: str) -> list[Receta]:
        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en RecetasRepository.%s: %s", contexto, exc)
            return []
        return [row_to_receta(row) for row in rows]
