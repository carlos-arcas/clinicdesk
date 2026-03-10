from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from clinicdesk.app.application.auditoria.audit_service import AuditEvent
from clinicdesk.app.application.auditoria_acceso import (
    AccionAuditoriaAcceso,
    EntidadAuditoriaAcceso,
    EventoAuditoriaAcceso,
)
from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_accesos import RepositorioAuditoriaAccesoSqlite
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_eventos import RepositorioAuditoriaEventosSqlite
from clinicdesk.app.infrastructure.sqlite.repos_telemetria_eventos import RepositorioTelemetriaEventosSqlite


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"


def _seed_auditoria(db_connection: sqlite3.Connection) -> int:
    repo = RepositorioAuditoriaAccesoSqlite(db_connection)
    repo.registrar(
        EventoAuditoriaAcceso(
            timestamp_utc="2026-01-01T10:11:12+00:00",
            usuario="admin",
            modo_demo=False,
            accion=AccionAuditoriaAcceso.VER_DETALLE_CITA,
            entidad_tipo=EntidadAuditoriaAcceso.CITA,
            entidad_id="15",
        )
    )
    row = db_connection.execute("SELECT id FROM auditoria_accesos ORDER BY id DESC LIMIT 1").fetchone()
    assert row is not None
    return int(row["id"])


def _seed_auditoria_eventos(db_connection: sqlite3.Connection) -> int:
    repo = RepositorioAuditoriaEventosSqlite(db_connection)
    repo.append(
        AuditEvent(
            action="cita_open",
            outcome="ok",
            actor_username="admin",
            actor_role="staff",
            correlation_id="corr-append-only",
            metadata={"origen": "tests"},
            timestamp_utc="2026-01-01T10:11:13+00:00",
        )
    )
    row = db_connection.execute("SELECT id FROM auditoria_eventos ORDER BY id DESC LIMIT 1").fetchone()
    assert row is not None
    return int(row["id"])


def _seed_telemetria(db_connection: sqlite3.Connection) -> int:
    repo = RepositorioTelemetriaEventosSqlite(db_connection)
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
    row = db_connection.execute("SELECT id FROM telemetria_eventos ORDER BY id DESC LIMIT 1").fetchone()
    assert row is not None
    return int(row["id"])


def test_tablas_sensibles_siguen_permitiendo_insertar_en_boundary(db_connection: sqlite3.Connection) -> None:
    _seed_auditoria(db_connection)
    _seed_telemetria(db_connection)
    _seed_auditoria_eventos(db_connection)

    total_auditoria = db_connection.execute("SELECT COUNT(*) FROM auditoria_accesos").fetchone()[0]
    total_telemetria = db_connection.execute("SELECT COUNT(*) FROM telemetria_eventos").fetchone()[0]
    total_auditoria_eventos = db_connection.execute("SELECT COUNT(*) FROM auditoria_eventos").fetchone()[0]

    assert total_auditoria == 1
    assert total_telemetria == 1
    assert total_auditoria_eventos == 1


@pytest.mark.parametrize(
    ("sql", "error_esperado"),
    [
        ("UPDATE auditoria_accesos SET usuario = 'otro' WHERE id = ?", "auditoria_accesos_append_only"),
        ("DELETE FROM auditoria_accesos WHERE id = ?", "auditoria_accesos_append_only"),
        ("UPDATE telemetria_eventos SET usuario = 'otro' WHERE id = ?", "telemetria_eventos_append_only"),
        ("DELETE FROM telemetria_eventos WHERE id = ?", "telemetria_eventos_append_only"),
        ("UPDATE auditoria_eventos SET action = 'otro' WHERE id = ?", "auditoria_eventos_append_only"),
        ("DELETE FROM auditoria_eventos WHERE id = ?", "auditoria_eventos_append_only"),
    ],
)
def test_tablas_sensibles_bloquean_update_delete_directo(
    db_connection: sqlite3.Connection,
    sql: str,
    error_esperado: str,
) -> None:
    auditoria_id = _seed_auditoria(db_connection)
    telemetria_id = _seed_telemetria(db_connection)
    auditoria_eventos_id = _seed_auditoria_eventos(db_connection)
    if "auditoria_accesos" in sql:
        objetivo_id = auditoria_id
    elif "auditoria_eventos" in sql:
        objetivo_id = auditoria_eventos_id
    else:
        objetivo_id = telemetria_id

    with pytest.raises(sqlite3.IntegrityError, match=error_esperado):
        db_connection.execute(sql, (objetivo_id,))

    row = db_connection.execute("SELECT usuario FROM auditoria_accesos WHERE id = ?", (auditoria_id,)).fetchone()
    assert row is not None and row["usuario"] == "admin"

    row = db_connection.execute("SELECT usuario FROM telemetria_eventos WHERE id = ?", (telemetria_id,)).fetchone()
    assert row is not None and row["usuario"] == "tester"

    row = db_connection.execute("SELECT action FROM auditoria_eventos WHERE id = ?", (auditoria_eventos_id,)).fetchone()
    assert row is not None and row["action"] == "cita_open"


def test_schema_append_only_es_idempotente_y_deja_triggers_activos() -> None:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    con.executescript(schema)
    con.executescript(schema)

    triggers = {
        row["name"]
        for row in con.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'trigger'
              AND name IN (
                'trg_auditoria_accesos_no_update',
                'trg_auditoria_accesos_no_delete',
                'trg_auditoria_eventos_no_update',
                'trg_auditoria_eventos_no_delete',
                'trg_telemetria_eventos_no_update',
                'trg_telemetria_eventos_no_delete'
              )
            """
        ).fetchall()
    }

    assert triggers == {
        "trg_auditoria_accesos_no_update",
        "trg_auditoria_accesos_no_delete",
        "trg_auditoria_eventos_no_update",
        "trg_auditoria_eventos_no_delete",
        "trg_telemetria_eventos_no_update",
        "trg_telemetria_eventos_no_delete",
    }
