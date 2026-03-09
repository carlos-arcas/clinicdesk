from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
from clinicdesk.app.application.usecases.obtener_resumen_telemetria_semana import ObtenerResumenTelemetriaSemana
from clinicdesk.app.application.usecases.preflight_integridad_telemetria import IntegridadTelemetriaComprometidaError
from clinicdesk.app.infrastructure.sqlite.auditoria_integridad import (
    ensure_telemetria_integridad_schema,
    verificar_cadena_telemetria,
)
from clinicdesk.app.infrastructure.sqlite.repos_telemetria_eventos import RepositorioTelemetriaEventosSqlite
from clinicdesk.app.queries.telemetria_eventos_queries import TelemetriaEventosQueries

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"


def _new_connection(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path.as_posix())
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    ensure_telemetria_integridad_schema(con)
    con.commit()
    return con


def test_telemetria_cadena_ok_y_detecta_tampering_en_contexto_anidado(tmp_path: Path) -> None:
    con = _new_connection(tmp_path / "telemetry.sqlite")
    repo = RepositorioTelemetriaEventosSqlite(con)

    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-01T10:00:00+00:00",
            usuario="tester",
            modo_demo=False,
            evento="gestion_abrir_cita",
            contexto='{"page":"agenda","filtros":{"estado":"abierta"}}',
            entidad_tipo="cita",
            entidad_id="10",
        )
    )
    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-01T10:01:00+00:00",
            usuario="tester",
            modo_demo=False,
            evento="auditoria_export",
            contexto='{"page":"auditoria","detalle":{"tab":"resumen"}}',
            entidad_tipo="auditoria",
            entidad_id="11",
        )
    )

    assert verificar_cadena_telemetria(con).ok is True

    con.execute("DROP TRIGGER IF EXISTS trg_telemetria_eventos_no_update")
    con.execute(
        """
        UPDATE telemetria_eventos
        SET contexto = '{"page":"auditoria","detalle":{"tab":"manipulado"}}'
        WHERE id = 2
        """
    )
    con.commit()

    resultado = verificar_cadena_telemetria(con)
    assert resultado.ok is False
    assert resultado.tabla == "telemetria_eventos"
    assert resultado.primer_fallo_id == 2


def test_telemetria_schema_integridad_es_idempotente_y_resumen_se_mantiene(tmp_path: Path) -> None:
    con = _new_connection(tmp_path / "telemetry-idempotent.sqlite")

    ensure_telemetria_integridad_schema(con)
    ensure_telemetria_integridad_schema(con)
    con.commit()

    columnas = {
        row["name"]
        for row in con.execute("PRAGMA table_info(telemetria_eventos)").fetchall()
        if row["name"] in {"prev_hash", "entry_hash"}
    }
    assert columnas == {"prev_hash", "entry_hash"}

    repo = RepositorioTelemetriaEventosSqlite(con)
    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-07T12:00:00+00:00",
            usuario="u1",
            modo_demo=False,
            evento="gestion_abrir_cita",
            contexto="page=gestion",
            entidad_tipo="cita",
            entidad_id="20",
        )
    )

    top = TelemetriaEventosQueries(con).top_eventos_por_rango(
        "2026-01-07T00:00:00+00:00",
        "2026-01-07T23:59:59+00:00",
        limit=5,
    )
    assert top and top[0].evento == "gestion_abrir_cita"
    assert verificar_cadena_telemetria(con).ok is True


def test_telemetria_legacy_sin_hash_chain_se_backfillea_y_verifica_en_preflight(tmp_path: Path) -> None:
    db_path = tmp_path / "telemetry-legacy.sqlite"
    con = sqlite3.connect(db_path.as_posix())
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
    con.execute(
        """
        INSERT INTO telemetria_eventos(timestamp_utc, usuario, modo_demo, evento, contexto, entidad_tipo, entidad_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "2026-01-01T10:00:00+00:00",
            "legacy",
            0,
            "gestion_abrir_cita",
            '{"page":"agenda"}',
            "cita",
            "1",
        ),
    )
    con.commit()

    resultado = TelemetriaEventosQueries(con).verificar_integridad_telemetria()
    assert resultado.ok is True

    fila_legacy = con.execute("SELECT prev_hash, entry_hash FROM telemetria_eventos WHERE id = 1").fetchone()
    assert fila_legacy["prev_hash"] == "GENESIS"
    assert fila_legacy["entry_hash"]

    repo = RepositorioTelemetriaEventosSqlite(con)
    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-01T10:01:00+00:00",
            usuario="nuevo",
            modo_demo=False,
            evento="auditoria_export",
            contexto='{"page":"auditoria"}',
            entidad_tipo="auditoria",
            entidad_id="2",
        )
    )

    filas = con.execute("SELECT id, prev_hash, entry_hash FROM telemetria_eventos ORDER BY id ASC").fetchall()
    assert filas[1]["prev_hash"] == filas[0]["entry_hash"]
    assert TelemetriaEventosQueries(con).verificar_integridad_telemetria().ok is True


def test_telemetria_legacy_backfill_es_idempotente(tmp_path: Path) -> None:
    con = sqlite3.connect((tmp_path / "telemetry-legacy-idempotent.sqlite").as_posix())
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
        INSERT INTO telemetria_eventos(timestamp_utc, usuario, modo_demo, evento, contexto, entidad_tipo, entidad_id)
        VALUES ('2026-01-01T10:00:00+00:00', 'legacy', 0, 'evento_legacy', NULL, NULL, NULL);
        """
    )

    ensure_telemetria_integridad_schema(con)
    con.commit()
    hashes_1 = con.execute("SELECT prev_hash, entry_hash FROM telemetria_eventos WHERE id = 1").fetchone()

    ensure_telemetria_integridad_schema(con)
    con.commit()
    hashes_2 = con.execute("SELECT prev_hash, entry_hash FROM telemetria_eventos WHERE id = 1").fetchone()

    assert hashes_1["prev_hash"] == hashes_2["prev_hash"] == "GENESIS"
    assert hashes_1["entry_hash"] == hashes_2["entry_hash"]


def test_resumen_telemetria_exige_preflight_y_funciona_si_cadena_esta_sana(tmp_path: Path) -> None:
    con = _new_connection(tmp_path / "telemetry-read-ok.sqlite")
    repo = RepositorioTelemetriaEventosSqlite(con)
    ahora = datetime.now(UTC).isoformat()
    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc=ahora,
            usuario="u1",
            modo_demo=False,
            evento="gestion_abrir_cita",
            contexto="page=gestion",
            entidad_tipo="cita",
            entidad_id="20",
        )
    )

    queries = TelemetriaEventosQueries(con)
    resumen = ObtenerResumenTelemetriaSemana(queries, verificador_integridad=queries).ejecutar()

    assert resumen.top_eventos
    assert resumen.top_eventos[0].evento == "gestion_abrir_cita"


def test_resumen_telemetria_falla_si_cadena_esta_manipulada(tmp_path: Path) -> None:
    con = _new_connection(tmp_path / "telemetry-read-fail.sqlite")
    repo = RepositorioTelemetriaEventosSqlite(con)
    ahora = datetime.now(UTC).isoformat()
    repo.registrar(
        EventoTelemetriaDTO(
            timestamp_utc=ahora,
            usuario="u1",
            modo_demo=False,
            evento="gestion_abrir_cita",
            contexto="page=gestion",
            entidad_tipo="cita",
            entidad_id="20",
        )
    )

    con.execute("DROP TRIGGER IF EXISTS trg_telemetria_eventos_no_update")
    con.execute("UPDATE telemetria_eventos SET evento = 'evento_manipulado' WHERE id = 1")
    con.commit()

    queries = TelemetriaEventosQueries(con)
    with pytest.raises(IntegridadTelemetriaComprometidaError) as exc:
        ObtenerResumenTelemetriaSemana(queries, verificador_integridad=queries).ejecutar()

    assert exc.value.reason_code == "telemetria_integridad_comprometida"
    assert exc.value.tabla == "telemetria_eventos"
    assert exc.value.primer_fallo_id == 1
