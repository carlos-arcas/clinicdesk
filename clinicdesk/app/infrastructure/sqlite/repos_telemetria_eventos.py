from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from clinicdesk.app.application.telemetria import EventoTelemetriaDTO


@dataclass(slots=True)
class RepositorioTelemetriaEventosSqlite:
    connection: sqlite3.Connection

    def registrar(self, evento: EventoTelemetriaDTO) -> None:
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
                evento.usuario,
                1 if evento.modo_demo else 0,
                evento.evento,
                evento.contexto,
                evento.entidad_tipo,
                evento.entidad_id,
            ),
        )
        self.connection.commit()
