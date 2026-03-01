from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from clinicdesk.app.application.auditoria_acceso import EventoAuditoriaAcceso


@dataclass(slots=True)
class RepositorioAuditoriaAccesoSqlite:
    connection: sqlite3.Connection

    def registrar(self, evento: EventoAuditoriaAcceso) -> None:
        metadata_json = json.dumps(evento.metadata_json, ensure_ascii=False) if evento.metadata_json else None
        self.connection.execute(
            """
            INSERT INTO auditoria_accesos(
                timestamp_utc,
                usuario,
                modo_demo,
                accion,
                entidad_tipo,
                entidad_id,
                metadata_json,
                created_at_utc
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evento.timestamp_utc,
                evento.usuario,
                1 if evento.modo_demo else 0,
                evento.accion.value,
                evento.entidad_tipo.value,
                evento.entidad_id,
                metadata_json,
                evento.timestamp_utc,
            ),
        )
        self.connection.commit()
