from __future__ import annotations

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.auditoria.page import PageAuditoria
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.pages.pages_registry import PageRegistry


def register(registry: PageRegistry, container: AppContainer) -> None:
    registry.register(
        PageDef(
            key="auditoria",
            title="Auditoría",
            factory=lambda: PageAuditoria(container.connection),
        )
    )
