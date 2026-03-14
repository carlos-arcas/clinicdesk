from __future__ import annotations

import sqlite3
from typing import Any

from clinicdesk.app.application.services.seguimiento_operativo_ml_service import (
    AccionHumanaItemML,
    EstadoSeguimientoItemML,
    HistorialDecisionML,
)


class RepositorioSeguimientoOperativoMLSqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def registrar_decision(self, decision: HistorialDecisionML) -> None:
        self._con.execute(
            """
            INSERT INTO ml_acciones_operativas(
                cita_id,
                prioridad_ml,
                accion_sugerida_ml,
                accion_humana,
                estado,
                nota_corta,
                timestamp_utc,
                actor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision.cita_id,
                decision.prioridad_ml,
                decision.accion_sugerida_ml,
                decision.accion_humana.value,
                decision.estado.value,
                decision.nota_corta,
                decision.timestamp_utc,
                decision.actor,
            ),
        )
        self._con.commit()

    def obtener_historial(self, cita_id: str) -> tuple[HistorialDecisionML, ...]:
        rows = self._con.execute(
            """
            SELECT cita_id, prioridad_ml, accion_sugerida_ml, accion_humana, estado, nota_corta, timestamp_utc, actor
            FROM ml_acciones_operativas
            WHERE cita_id = ?
            ORDER BY id ASC
            """,
            (cita_id,),
        ).fetchall()
        return tuple(self._row_to_historial(row) for row in rows)

    def _row_to_historial(self, row: Any) -> HistorialDecisionML:
        return HistorialDecisionML(
            cita_id=str(row["cita_id"]),
            prioridad_ml=str(row["prioridad_ml"]),
            accion_sugerida_ml=str(row["accion_sugerida_ml"]),
            accion_humana=AccionHumanaItemML(str(row["accion_humana"])),
            estado=EstadoSeguimientoItemML(str(row["estado"])),
            nota_corta=str(row["nota_corta"] or ""),
            timestamp_utc=str(row["timestamp_utc"]),
            actor=str(row["actor"] or "operador"),
        )
