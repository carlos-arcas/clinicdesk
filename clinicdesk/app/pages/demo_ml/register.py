from __future__ import annotations

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.demo_ml.page import PageDemoML
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.pages.pages_registry import PageRegistry


def register(registry: PageRegistry, container: AppContainer) -> None:
    registry.register(
        PageDef(
            key="demo_ml",
            title="Demo & ML",
            factory=lambda: PageDemoML(container.demo_ml_facade),
        )
    )
