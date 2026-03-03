from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.ports.telemetria_port import RepositorioTelemetria
from clinicdesk.app.application.security import UserContext
from clinicdesk.app.application.telemetria import EventoTelemetriaDTO, ahora_utc_iso
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class RegistrarTelemetria:
    repositorio: RepositorioTelemetria

    def ejecutar(
        self,
        *,
        contexto_usuario: UserContext,
        evento: str,
        contexto: str | None = None,
        entidad_tipo: str | None = None,
        entidad_id: int | str | None = None,
    ) -> None:
        evento_dto = EventoTelemetriaDTO(
            timestamp_utc=ahora_utc_iso(),
            usuario=contexto_usuario.username,
            modo_demo=contexto_usuario.demo_mode,
            evento=evento,
            contexto=contexto,
            entidad_tipo=entidad_tipo,
            entidad_id=str(entidad_id) if entidad_id is not None else None,
        )
        self.repositorio.registrar(evento_dto)
        LOGGER.info(
            "telemetria_evento",
            extra={"action": "telemetria_evento", "evento": evento, "entidad_tipo": entidad_tipo},
        )
