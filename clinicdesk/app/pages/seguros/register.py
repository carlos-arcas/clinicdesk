from __future__ import annotations

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.pages.pages_registry import PageRegistry
from clinicdesk.app.pages.seguros.page import PageSeguros


def register(registry: PageRegistry, _: AppContainer, i18n: I18nManager) -> None:
    registry.register(
        PageDef(
            key="seguros",
            title=i18n.t("nav.seguros"),
            factory=lambda: PageSeguros(i18n),
        )
    )
