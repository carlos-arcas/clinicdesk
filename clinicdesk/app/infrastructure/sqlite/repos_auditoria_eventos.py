from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from clinicdesk.app.application.auditoria.audit_service import AuditEvent
from clinicdesk.app.infrastructure.sqlite.auditoria_integridad import (
    ensure_auditoria_integridad_schema,
    siguiente_hash_evento,
)


@dataclass(slots=True)
class RepositorioAuditoriaEventosSqlite:
    connection: sqlite3.Connection

    def __post_init__(self) -> None:
        ensure_auditoria_integridad_schema(self.connection)

    def append(self, event: AuditEvent) -> None:
        metadata_json = json.dumps(event.metadata, ensure_ascii=False) if event.metadata else None
        payload = {
            "timestamp_utc": event.timestamp_utc,
            "action": event.action,
            "outcome": event.outcome,
            "actor_username": event.actor_username,
            "actor_role": event.actor_role,
            "correlation_id": event.correlation_id,
            "metadata_json": metadata_json,
        }
        prev_hash, entry_hash = siguiente_hash_evento(self.connection, payload)
        self.connection.execute(
            """
            INSERT INTO auditoria_eventos(
                timestamp_utc,
                action,
                outcome,
                actor_username,
                actor_role,
                correlation_id,
                metadata_json,
                prev_hash,
                entry_hash
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp_utc,
                event.action,
                event.outcome,
                event.actor_username,
                event.actor_role,
                event.correlation_id,
                metadata_json,
                prev_hash,
                entry_hash,
            ),
        )
        self.connection.commit()
