from __future__ import annotations

import sqlite3
from typing import Protocol

from clinicdesk.app.application.recordatorios.puertos import (
    DatosRecordatorioCitaDTO,
    EstadoRecordatorioDTO,
)
from clinicdesk.app.infrastructure.sqlite.pacientes.pii import decrypt_optional
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher


class RecordatoriosCitasSqliteGateway:
    def __init__(
        self, connection: sqlite3.Connection | None = None, proveedor_conexion: _ProveedorConexion | None = None
    ) -> None:
        if connection is None and proveedor_conexion is None:
            raise ValueError("Se requiere connection o proveedor_conexion")
        self._con = connection
        self._proveedor = proveedor_conexion

    def _has_crypto_columns(self) -> bool:
        con = self._obtener_conexion()
        columns = {row["name"] for row in con.execute("PRAGMA table_info(pacientes)").fetchall()}
        return {"telefono_enc", "email_enc"}.issubset(columns)

    def _contacto_paciente(self, row: sqlite3.Row) -> tuple[str | None, str | None]:
        con = self._obtener_conexion()
        protection = PacientesFieldProtection(con)
        pii_cipher = get_connection_pii_cipher(con)
        telefono = protection.decode(
            "telefono",
            legacy=decrypt_optional(pii_cipher, row["telefono"]),
            encrypted=row["telefono_enc"] if "telefono_enc" in row.keys() else None,
        )
        email = protection.decode(
            "email",
            legacy=decrypt_optional(pii_cipher, row["email"]),
            encrypted=row["email_enc"] if "email_enc" in row.keys() else None,
        )
        return telefono, email

    def obtener_datos_recordatorio_cita(self, cita_id: int) -> DatosRecordatorioCitaDTO | None:
        row = (
            self._obtener_conexion()
            .execute(
                self._sql_obtener_datos_cita(),
                (cita_id,),
            )
            .fetchone()
        )
        if row is None:
            return None
        telefono, email = self._contacto_paciente(row)
        return DatosRecordatorioCitaDTO(
            cita_id=int(row["cita_id"]),
            inicio=str(row["inicio"]),
            paciente_nombre=str(row["paciente_nombre"]),
            telefono=telefono,
            email=email,
            medico_nombre=row["medico_nombre"],
        )

    def _sql_obtener_datos_cita(self) -> str:
        if self._has_crypto_columns():
            return """
            SELECT
                c.id AS cita_id,
                c.inicio AS inicio,
                p.nombre || ' ' || p.apellidos AS paciente_nombre,
                p.telefono AS telefono,
                p.telefono_enc AS telefono_enc,
                p.email AS email,
                p.email_enc AS email_enc,
                m.nombre || ' ' || m.apellidos AS medico_nombre
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            WHERE c.id = ? AND c.activo = 1
            """
        return """
            SELECT
                c.id AS cita_id,
                c.inicio AS inicio,
                p.nombre || ' ' || p.apellidos AS paciente_nombre,
                p.telefono AS telefono,
                NULL AS telefono_enc,
                p.email AS email,
                NULL AS email_enc,
                m.nombre || ' ' || m.apellidos AS medico_nombre
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            WHERE c.id = ? AND c.activo = 1
            """

    def upsert_recordatorio_cita(self, cita_id: int, canal: str, estado: str, now_utc: str) -> None:
        self._obtener_conexion().execute(
            _SQL_UPSERT_RECORDATORIO,
            (cita_id, canal, estado, now_utc, now_utc),
        )

    def obtener_estado_recordatorio(self, cita_id: int) -> tuple[EstadoRecordatorioDTO, ...]:
        rows = (
            self._obtener_conexion()
            .execute(
                """
            SELECT canal, estado, updated_at_utc
            FROM recordatorios_citas
            WHERE cita_id = ?
            ORDER BY updated_at_utc DESC
            """,
                (cita_id,),
            )
            .fetchall()
        )
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
        rows = (
            self._obtener_conexion()
            .execute(
                self._sql_contacto_lote(cita_ids),
                cita_ids,
            )
            .fetchall()
        )
        return {int(row["cita_id"]): self._contacto_paciente(row) for row in rows}

    def _sql_contacto_lote(self, cita_ids: tuple[int, ...]) -> str:
        if self._has_crypto_columns():
            return f"""
            SELECT c.id AS cita_id, p.telefono AS telefono, p.telefono_enc AS telefono_enc, p.email AS email, p.email_enc AS email_enc
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            WHERE c.id IN ({_placeholders(cita_ids)}) AND c.activo = 1
            """
        return f"""
            SELECT c.id AS cita_id, p.telefono AS telefono, NULL AS telefono_enc, p.email AS email, NULL AS email_enc
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            WHERE c.id IN ({_placeholders(cita_ids)}) AND c.activo = 1
            """

    def obtener_estado_recordatorio_lote(self, cita_ids: tuple[int, ...]) -> dict[tuple[int, str], str]:
        if not cita_ids:
            return {}
        rows = (
            self._obtener_conexion()
            .execute(
                f"""
            SELECT cita_id, canal, estado
            FROM recordatorios_citas
            WHERE cita_id IN ({_placeholders(cita_ids)})
            """,
                cita_ids,
            )
            .fetchall()
        )
        return {(int(row["cita_id"]), str(row["canal"])): str(row["estado"]) for row in rows}

    def upsert_recordatorios_lote(self, items: list[tuple[int, str, str, str]]) -> int:
        if not items:
            return 0
        params = [(cita_id, canal, estado, now_utc, now_utc) for cita_id, canal, estado, now_utc in items]
        cursor = self._obtener_conexion().executemany(_SQL_UPSERT_RECORDATORIO, params)
        return cursor.rowcount if cursor.rowcount != -1 else len(items)

    def _obtener_conexion(self) -> sqlite3.Connection:
        if self._proveedor is not None:
            return self._proveedor.obtener()
        if self._con is None:
            raise RuntimeError("Conexión no inicializada")
        return self._con


class _ProveedorConexion(Protocol):
    def obtener(self) -> sqlite3.Connection: ...


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
