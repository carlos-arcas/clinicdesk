from __future__ import annotations

import sqlite3

from clinicdesk.app.queries.telemetria_eventos_queries import TelemetriaEventosQueries


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


def test_top_eventos_por_rango_devuelve_top5() -> None:
    con = _crear_conexion()
    datos = [
        ("2026-01-12T10:00:00+00:00", "u1", 0, "gestion_abrir_cita"),
        ("2026-01-12T10:01:00+00:00", "u1", 0, "gestion_abrir_cita"),
        ("2026-01-12T10:02:00+00:00", "u1", 0, "citas_intent_aplicado"),
        ("2026-01-12T10:03:00+00:00", "u1", 0, "auditoria_export"),
    ]
    con.executemany(
        "INSERT INTO telemetria_eventos(timestamp_utc, usuario, modo_demo, evento) VALUES(?, ?, ?, ?)",
        datos,
    )
    q = TelemetriaEventosQueries(con)

    top = q.top_eventos_por_rango("2026-01-12T00:00:00+00:00", "2026-01-12T23:59:59+00:00", limit=5)

    assert len(top) == 3
    assert top[0].evento == "gestion_abrir_cita"
    assert top[0].total == 2
