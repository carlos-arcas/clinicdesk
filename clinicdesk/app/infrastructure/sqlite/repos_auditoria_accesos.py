from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from clinicdesk.app.application.auditoria_acceso import EventoAuditoriaAcceso
from clinicdesk.app.infrastructure.sqlite.auditoria_integridad import (
    ensure_auditoria_integridad_schema,
    siguiente_hash_acceso,
)
from clinicdesk.app.infrastructure.sqlite.persistencia_segura_auditoria_telemetria import (
    sanear_evento_auditoria_para_persistencia,
)


@dataclass(slots=True)
class RepositorioAuditoriaAccesoSqlite:
    connection: sqlite3.Connection

    def __post_init__(self) -> None:
        ensure_auditoria_integridad_schema(self.connection)

    def registrar(self, evento: EventoAuditoriaAcceso) -> None:
        usuario_saneado, entidad_id_saneado, metadata_saneada, _ = sanear_evento_auditoria_para_persistencia(
            usuario=evento.usuario,
            entidad_id=evento.entidad_id,
            metadata_json=evento.metadata_json,
        )
        metadata_json = json.dumps(metadata_saneada, ensure_ascii=False) if metadata_saneada else None
        payload = {
            "timestamp_utc": evento.timestamp_utc,
            "usuario": usuario_saneado,
            "modo_demo": 1 if evento.modo_demo else 0,
            "accion": evento.accion.value,
            "entidad_tipo": evento.entidad_tipo.value,
            "entidad_id": entidad_id_saneado,
            "metadata_json": metadata_json,
            "created_at_utc": evento.timestamp_utc,
        }
        prev_hash, entry_hash = siguiente_hash_acceso(self.connection, payload)
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
                created_at_utc,
                prev_hash,
                entry_hash
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evento.timestamp_utc,
                usuario_saneado,
                1 if evento.modo_demo else 0,
                evento.accion.value,
                evento.entidad_tipo.value,
                entidad_id_saneado,
                metadata_json,
                evento.timestamp_utc,
                prev_hash,
                entry_hash,
            ),
        )
        self.connection.commit()
