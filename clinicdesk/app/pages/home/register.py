from __future__ import annotations

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.pages.pages_registry import PageRegistry
from clinicdesk.app.pages.home.page import PageHome


def register(registry: PageRegistry, container: AppContainer, i18n: I18nManager) -> None:
    registry.register(
        PageDef(
            key="home",
            title=i18n.t("nav.home"),
            factory=lambda: PageHome(container=container, i18n=i18n),
        )
    )
