from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
from clinicdesk.app.infrastructure.sqlite.persistencia_segura_auditoria_telemetria import (
    sanear_contexto_telemetria_para_persistencia,
    sanear_evento_auditoria_para_persistencia,
)


@dataclass(slots=True)
class RepositorioTelemetriaEventosSqlite:
    connection: sqlite3.Connection

    def registrar(self, evento: EventoTelemetriaDTO) -> None:
        usuario_saneado, entidad_id_saneado, _, _ = sanear_evento_auditoria_para_persistencia(
            usuario=evento.usuario,
            entidad_id=evento.entidad_id or "",
            metadata_json=None,
        )
        contexto_saneado, redaccion_aplicada = sanear_contexto_telemetria_para_persistencia(evento.contexto)
        if redaccion_aplicada and contexto_saneado and "redaccion_aplicada" not in contexto_saneado:
            contexto_saneado = f"{contexto_saneado};redaccion_aplicada=true"

        entidad_id_para_guardar = entidad_id_saneado if evento.entidad_id is not None else None

        self.connection.execute(
            """
            INSERT INTO telemetria_eventos(
                timestamp_utc,
                usuario,
                modo_demo,
                evento,
                contexto,
                entidad_tipo,
                entidad_id
            )
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evento.timestamp_utc,
                usuario_saneado,
                1 if evento.modo_demo else 0,
                evento.evento,
                contexto_saneado,
                evento.entidad_tipo,
                entidad_id_para_guardar,
            ),
        )
        self.connection.commit()
