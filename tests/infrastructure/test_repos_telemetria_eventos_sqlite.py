from __future__ import annotations

import json
import sqlite3

from clinicdesk.app.application.security import Role, UserContext
from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
from clinicdesk.app.application.usecases.registrar_telemetria import RegistrarTelemetria
from clinicdesk.app.infrastructure.sqlite.repos_telemetria_eventos import RepositorioTelemetriaEventosSqlite


def _crear_conexion() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE telemetria_eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            usuario TEXT NOT NULL,
            modo_demo INTEGER NOT NULL,
            evento TEXT NOT NULL,
            contexto TEXT,
            entidad_tipo TEXT,
            entidad_id TEXT
        );
        """
    )
    return con


def test_registrar_evento_telemetria_sqlite() -> None:
    con = _crear_conexion()
    repo = RepositorioTelemetriaEventosSqlite(con)

    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-10T12:00:00+00:00",
            usuario="tester",
            modo_demo=False,
            evento="gestion_abrir_cita",
            contexto="page=gestion",
            entidad_tipo="cita",
            entidad_id="88",
        )
    )

    row = con.execute("SELECT evento, contexto, entidad_id FROM telemetria_eventos").fetchone()
    assert row is not None
    assert row["evento"] == "gestion_abrir_cita"
    assert row["contexto"] == "page=gestion"
    assert row["entidad_id"] == "88"


def test_repositorio_telemetria_sqlite_sanea_pii_directa_en_contexto_y_entidad_id() -> None:
    con = _crear_conexion()
    repo = RepositorioTelemetriaEventosSqlite(con)

    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-10T12:00:00+00:00",
            usuario="ana@example.com",
            modo_demo=False,
            evento="auditoria_export",
            contexto=json.dumps(
                {
                    "page": "auditoria",
                    "extra": {
                        "email": "ana@example.com",
                        "telefono": "600123123",
                        "historia_clinica": "HC-445566",
                        "direccion": "Avenida Salud 1",
                    },
                },
                ensure_ascii=False,
            ),
            entidad_tipo="auditoria",
            entidad_id="12345678Z",
        )
    )

    row = con.execute("SELECT usuario, contexto, entidad_id FROM telemetria_eventos").fetchone()
    assert row is not None
    assert "ana@example.com" not in row["usuario"]
    assert "12345678Z" not in row["entidad_id"]

    contexto = row["contexto"] or ""
    assert "ana@example.com" not in contexto
    assert "600123123" not in contexto
    assert "HC-445566" not in contexto
    assert "Avenida" not in contexto
    assert "redaccion_aplicada" in contexto


def test_usecase_y_repo_no_persisten_pii_en_contexto(db_connection) -> None:
    db_connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS telemetria_eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            usuario TEXT NOT NULL,
            modo_demo INTEGER NOT NULL,
            evento TEXT NOT NULL,
            contexto TEXT,
            entidad_tipo TEXT,
            entidad_id TEXT
        );
        """
    )
    repo = RepositorioTelemetriaEventosSqlite(db_connection)
    usecase = RegistrarTelemetria(repo)

    usecase.ejecutar(
        contexto_usuario=UserContext(role=Role.ADMIN, username="auditor", demo_mode=False),
        evento="auditoria_export",
        contexto="page=auditoria;detalle=email ana@test.com telefono 600123123;dni=12345678Z",
        entidad_tipo="auditoria",
        entidad_id=12,
    )

    row = db_connection.execute(
        """
        SELECT contexto
        FROM telemetria_eventos
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    assert row is not None
    contexto = row["contexto"] or ""
    assert "ana@test.com" not in contexto
    assert "600123123" not in contexto
    assert "12345678Z" not in contexto
    assert "[REDACTED_EMAIL]" in contexto
    assert "[REDACTED_PHONE]" in contexto
    assert "redaccion_aplicada=true" in contexto
