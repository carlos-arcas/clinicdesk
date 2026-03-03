from __future__ import annotations

import sqlite3

from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
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
