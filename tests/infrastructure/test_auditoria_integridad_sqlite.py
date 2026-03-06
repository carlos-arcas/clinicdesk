from __future__ import annotations

import sqlite3
from pathlib import Path

from clinicdesk.app.application.auditoria.audit_service import AuditEvent
from clinicdesk.app.infrastructure.sqlite.auditoria_integridad import (
    ensure_auditoria_integridad_schema,
    verificar_cadena,
)
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_eventos import RepositorioAuditoriaEventosSqlite


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"


def _new_connection(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path.as_posix())
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    ensure_auditoria_integridad_schema(con)
    con.commit()
    return con


def _build_event(action: str, stamp: str) -> AuditEvent:
    return AuditEvent(
        action=action,
        outcome="ok",
        actor_username="admin",
        actor_role="ADMIN",
        correlation_id="cid-1",
        metadata={"seed": 7},
        timestamp_utc=stamp,
    )


def test_verificar_cadena_ok_y_detecta_tampering(tmp_path: Path) -> None:
    con = _new_connection(tmp_path / "audit.sqlite")
    repo = RepositorioAuditoriaEventosSqlite(con)

    repo.append(_build_event("LOGIN", "2026-01-01T10:00:00+00:00"))
    repo.append(_build_event("OPEN_PATIENT", "2026-01-01T10:01:00+00:00"))
    repo.append(_build_event("EXPORT", "2026-01-01T10:02:00+00:00"))

    assert verificar_cadena(con).ok is True

    con.execute("UPDATE auditoria_eventos SET action = 'ALTERADO' WHERE id = 2")
    con.commit()
    resultado_campo = verificar_cadena(con)
    assert resultado_campo.ok is False
    assert resultado_campo.primer_fallo_id == 2

    con.execute("UPDATE auditoria_eventos SET action = 'OPEN_PATIENT' WHERE id = 2")
    con.execute("UPDATE auditoria_eventos SET prev_hash = 'X', entry_hash = 'Y' WHERE id = 3")
    con.commit()

    resultado_hash = verificar_cadena(con)
    assert resultado_hash.ok is False
    assert resultado_hash.primer_fallo_id == 3

    con.close()
