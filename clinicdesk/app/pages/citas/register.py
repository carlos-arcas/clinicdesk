from __future__ import annotations

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.pages.citas.page import PageCitas


def register(registry: PageRegistry, container: AppContainer) -> None:
    registry.register(
        PageDef(
            key="citas",
            title="Citas",
            factory=lambda: PageCitas(container),
        )
    )
