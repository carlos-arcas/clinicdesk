from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from clinicdesk.app.application.auditoria.audit_service import AuditEvent


@dataclass(slots=True)
class RepositorioAuditoriaEventosSqlite:
    connection: sqlite3.Connection

    def append(self, event: AuditEvent) -> None:
        metadata_json = json.dumps(event.metadata, ensure_ascii=False) if event.metadata else None
        self.connection.execute(
            """
            INSERT INTO auditoria_eventos(
                timestamp_utc,
                action,
                outcome,
                actor_username,
                actor_role,
                correlation_id,
                metadata_json
            )
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_utc,
                event.action,
                event.outcome,
                event.actor_username,
                event.actor_role,
                event.correlation_id,
                metadata_json,
            ),
        )
        self.connection.commit()
