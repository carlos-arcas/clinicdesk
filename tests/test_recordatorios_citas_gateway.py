from __future__ import annotations

import sqlite3
from pathlib import Path

from clinicdesk.app.infrastructure.sqlite.recordatorios_citas_gateway import RecordatoriosCitasSqliteGateway


def _build_connection() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    schema_path = Path("clinicdesk/app/infrastructure/sqlite/schema.sql")
    con.executescript(schema_path.read_text(encoding="utf-8"))
    _seed_minimo(con)
    return con


def _seed_minimo(con: sqlite3.Connection) -> None:
    con.execute(
        """
        INSERT INTO pacientes(tipo_documento, documento, nombre, apellidos, telefono, email, activo)
        VALUES ('DNI', '123', 'Ana', 'Pérez', '600000000', 'ana@test.com', 1)
        """
    )
    con.execute(
        """
        INSERT INTO medicos(tipo_documento, documento, nombre, apellidos, num_colegiado, especialidad, activo)
        VALUES ('DNI', '456', 'Luis', 'López', 'COL1', 'General', 1)
        """
    )
    con.execute("INSERT INTO salas(nombre, tipo, ubicacion, activa) VALUES ('Sala 1', 'CONSULTA', 'P1', 1)")
    con.execute(
        """
        INSERT INTO citas(paciente_id, medico_id, sala_id, inicio, fin, estado, motivo, activo)
        VALUES (1, 1, 1, '2026-01-02T10:30:00', '2026-01-02T11:00:00', 'PROGRAMADA', 'Control', 1)
        """
    )


def test_upsert_recordatorio_cita_actualiza_estado_y_evitar_duplicados() -> None:
    con = _build_connection()
    gateway = RecordatoriosCitasSqliteGateway(con)

    gateway.upsert_recordatorio_cita(1, "WHATSAPP", "PREPARADO", "2026-01-01T10:00:00+00:00")
    gateway.upsert_recordatorio_cita(1, "WHATSAPP", "ENVIADO", "2026-01-01T11:00:00+00:00")

    rows = con.execute("SELECT canal, estado, created_at_utc, updated_at_utc FROM recordatorios_citas").fetchall()
    assert len(rows) == 1
    assert rows[0]["canal"] == "WHATSAPP"
    assert rows[0]["estado"] == "ENVIADO"
    assert rows[0]["created_at_utc"] == "2026-01-01T10:00:00+00:00"
    assert rows[0]["updated_at_utc"] == "2026-01-01T11:00:00+00:00"


def test_obtener_estado_recordatorio_por_canal() -> None:
    con = _build_connection()
    gateway = RecordatoriosCitasSqliteGateway(con)
    gateway.upsert_recordatorio_cita(1, "EMAIL", "PREPARADO", "2026-01-01T10:00:00+00:00")

    estados = gateway.obtener_estado_recordatorio(1)

    assert len(estados) == 1
    assert estados[0].canal == "EMAIL"
    assert estados[0].estado == "PREPARADO"
