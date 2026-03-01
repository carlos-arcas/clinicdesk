from __future__ import annotations

from typing import Protocol

from clinicdesk.app.application.auditoria_acceso import EventoAuditoriaAcceso


class RepositorioAuditoriaAcceso(Protocol):
    def registrar(self, evento: EventoAuditoriaAcceso) -> None:
        ...
