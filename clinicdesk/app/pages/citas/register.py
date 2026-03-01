from __future__ import annotations

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.page import PageCitas
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.pages.pages_registry import PageRegistry


def register(registry: PageRegistry, container: AppContainer, i18n: I18nManager) -> None:
    registry.register(
        PageDef(
            key="citas",
            title="Citas",
            factory=lambda: PageCitas(container, i18n),
        )
    )
