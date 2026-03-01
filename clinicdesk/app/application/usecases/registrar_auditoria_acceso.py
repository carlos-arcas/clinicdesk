from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.auditoria_acceso import (
    AccionAuditoriaAcceso,
    EntidadAuditoriaAcceso,
    EventoAuditoriaAcceso,
    now_utc_iso,
)
from clinicdesk.app.application.ports.auditoria_acceso_port import RepositorioAuditoriaAcceso
from clinicdesk.app.application.security import UserContext
from clinicdesk.app.bootstrap_logging import get_logger


LOGGER = get_logger(__name__)


@dataclass(slots=True)
class RegistrarAuditoriaAcceso:
    repositorio: RepositorioAuditoriaAcceso

    def execute(
        self,
        *,
        contexto_usuario: UserContext,
        accion: AccionAuditoriaAcceso,
        entidad_tipo: EntidadAuditoriaAcceso,
        entidad_id: int | str,
        metadata: dict[str, str | int | float | bool | None] | None = None,
    ) -> None:
        evento = EventoAuditoriaAcceso(
            timestamp_utc=now_utc_iso(),
            usuario=contexto_usuario.username,
            modo_demo=contexto_usuario.demo_mode,
            accion=accion,
            entidad_tipo=entidad_tipo,
            entidad_id=str(entidad_id),
            metadata_json=metadata,
        )
        self.repositorio.registrar(evento)
        LOGGER.info(
            "auditoria_acceso_registrada accion=%s entidad=%s entidad_id=%s",
            accion.value,
            entidad_tipo.value,
            evento.entidad_id,
        )
