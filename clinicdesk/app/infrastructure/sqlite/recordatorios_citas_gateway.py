from __future__ import annotations

import sqlite3

from clinicdesk.app.application.ports.recordatorios_citas_port import (
    DatosRecordatorioCitaDTO,
    EstadoRecordatorioDTO,
)


class RecordatoriosCitasSqliteGateway:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def obtener_datos_recordatorio_cita(self, cita_id: int) -> DatosRecordatorioCitaDTO | None:
        row = self._con.execute(
            """
            SELECT
                c.id AS cita_id,
                c.inicio AS inicio,
                p.nombre || ' ' || p.apellidos AS paciente_nombre,
                p.telefono AS telefono,
                p.email AS email,
                m.nombre || ' ' || m.apellidos AS medico_nombre
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            WHERE c.id = ? AND c.activo = 1
            """,
            (cita_id,),
        ).fetchone()
        if row is None:
            return None
        return DatosRecordatorioCitaDTO(
            cita_id=int(row["cita_id"]),
            inicio=str(row["inicio"]),
            paciente_nombre=str(row["paciente_nombre"]),
            telefono=row["telefono"],
            email=row["email"],
            medico_nombre=row["medico_nombre"],
        )

    def upsert_recordatorio_cita(self, cita_id: int, canal: str, estado: str, now_utc: str) -> None:
        self._con.execute(
            _SQL_UPSERT_RECORDATORIO,
            (cita_id, canal, estado, now_utc, now_utc),
        )

    def obtener_estado_recordatorio(self, cita_id: int) -> tuple[EstadoRecordatorioDTO, ...]:
        rows = self._con.execute(
            """
            SELECT canal, estado, updated_at_utc
            FROM recordatorios_citas
            WHERE cita_id = ?
            ORDER BY updated_at_utc DESC
            """,
            (cita_id,),
        ).fetchall()
        latest: dict[str, EstadoRecordatorioDTO] = {}
        for row in rows:
            canal = str(row["canal"])
            if canal in latest:
                continue
            latest[canal] = EstadoRecordatorioDTO(
                canal=canal,
                estado=str(row["estado"]),
                updated_at_utc=str(row["updated_at_utc"]),
            )
        return tuple(latest.values())

    def obtener_contacto_citas(self, cita_ids: tuple[int, ...]) -> dict[int, tuple[str | None, str | None]]:
        if not cita_ids:
            return {}
        rows = self._con.execute(
            f"""
            SELECT c.id AS cita_id, p.telefono AS telefono, p.email AS email
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            WHERE c.id IN ({_placeholders(cita_ids)}) AND c.activo = 1
            """,
            cita_ids,
        ).fetchall()
        return {int(row["cita_id"]): (row["telefono"], row["email"]) for row in rows}

    def obtener_estado_recordatorio_lote(self, cita_ids: tuple[int, ...]) -> dict[tuple[int, str], str]:
        if not cita_ids:
            return {}
        rows = self._con.execute(
            f"""
            SELECT cita_id, canal, estado
            FROM recordatorios_citas
            WHERE cita_id IN ({_placeholders(cita_ids)})
            """,
            cita_ids,
        ).fetchall()
        return {(int(row["cita_id"]), str(row["canal"])): str(row["estado"]) for row in rows}

    def upsert_recordatorios_lote(self, items: list[tuple[int, str, str, str]]) -> int:
        if not items:
            return 0
        params = [(cita_id, canal, estado, now_utc, now_utc) for cita_id, canal, estado, now_utc in items]
        cursor = self._con.executemany(_SQL_UPSERT_RECORDATORIO, params)
        return cursor.rowcount if cursor.rowcount != -1 else len(items)


_SQL_UPSERT_RECORDATORIO = """
INSERT INTO recordatorios_citas (
    cita_id,
    canal,
    estado,
    created_at_utc,
    updated_at_utc
) VALUES (?, ?, ?, ?, ?)
ON CONFLICT(cita_id, canal)
DO UPDATE SET
    estado = excluded.estado,
    updated_at_utc = excluded.updated_at_utc
"""


def _placeholders(values: tuple[int, ...]) -> str:
    return ", ".join(["?"] * len(values))
