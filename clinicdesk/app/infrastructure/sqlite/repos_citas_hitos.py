from __future__ import annotations

import sqlite3
from datetime import datetime

from clinicdesk.app.domain.enums import CanalReserva, TipoCita
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.infrastructure.sqlite.sqlite_datetime_codecs import serialize_datetime


class CitasHitosRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def obtener_cita_por_id(self, cita_id: int) -> dict[str, object] | None:
        row = self._con.execute(
            """
            SELECT id, inicio, check_in_at, llamado_a_consulta_at, consulta_inicio_at, consulta_fin_at, check_out_at
            FROM citas
            WHERE id = ?
            """,
            (cita_id,),
        ).fetchone()
        return dict(row) if row else None

    def obtener_inicios_programados_por_cita_ids(self, cita_ids: tuple[int, ...]) -> dict[int, datetime]:
        if not cita_ids:
            return {}
        placeholders = ",".join("?" for _ in cita_ids)
        rows = self._con.execute(
            f"SELECT id, inicio FROM citas WHERE id IN ({placeholders})",
            cita_ids,
        ).fetchall()
        return {
            int(row["id"]): datetime.fromisoformat(str(row["inicio"]))
            for row in rows
            if row["inicio"] is not None
        }

    def actualizar_hito_atencion(self, cita_id: int, campo_timestamp: str, valor_datetime: datetime) -> bool:
        campos_permitidos = {
            "check_in_at",
            "llamado_a_consulta_at",
            "consulta_inicio_at",
            "consulta_fin_at",
            "check_out_at",
        }
        if campo_timestamp not in campos_permitidos:
            raise ValidationError("Campo de hito no permitido.")
        cur = self._con.execute(
            f"UPDATE citas SET {campo_timestamp} = ? WHERE id = ? AND {campo_timestamp} IS NULL",
            (serialize_datetime(valor_datetime), cita_id),
        )
        self._con.commit()
        return int(cur.rowcount) > 0

    def actualizar_contexto_cita(self, cita_id: int, tipo_cita: TipoCita | None, canal_reserva: CanalReserva | None) -> bool:
        cur = self._con.execute(
            "UPDATE citas SET tipo_cita = ?, canal_reserva = ? WHERE id = ?",
            (tipo_cita.value if tipo_cita else None, canal_reserva.value if canal_reserva else None, cita_id),
        )
        self._con.commit()
        return int(cur.rowcount) > 0
