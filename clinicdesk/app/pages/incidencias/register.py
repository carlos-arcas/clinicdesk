from __future__ import annotations

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.pages.pages_registry import PageRegistry
from clinicdesk.app.pages.incidencias.page import PageIncidencias


def register(registry: PageRegistry, container: AppContainer) -> None:
    registry.register(
        PageDef(
            key="incidencias",
            title="Incidencias",
            factory=lambda: PageIncidencias(container),
        )
    )
