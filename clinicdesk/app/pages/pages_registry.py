from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.page_def import PageDef


class PageRegistry:
    """Registro in-memory de PageDef.

    Cada feature/page registra su PageDef en un único lugar.
    La navegación (MainWindow) consume PageDef y crea widgets lazy vía factory().
    """

    def __init__(self) -> None:
        self._pages: Dict[str, PageDef] = {}

    def register(self, page: PageDef) -> None:
        if page.key in self._pages:
            raise ValueError(f"Página duplicada: {page.key}")
        self._pages[page.key] = page

    def get(self, key: str) -> PageDef:
        return self._pages[key]

    def list(self) -> List[PageDef]:
        # Orden estable por inserción
        return list(self._pages.values())

    def list_entries(self) -> List[PageDef]:
        return self.list()


def register_pages(registry: PageRegistry, container: AppContainer) -> None:
    from clinicdesk.app.pages.citas.register import register as register_citas
    from clinicdesk.app.pages.farmacia.register import register as register_farmacia
    from clinicdesk.app.pages.home.register import register as register_home

    register_home(registry, container)
    register_citas(registry, container)
    register_farmacia(registry, container)


def get_pages(container: AppContainer) -> List[PageDef]:
    """Bootstrap UI: reúne todas las páginas registradas por feature."""
    reg = PageRegistry()
    register_pages(reg, container)
    return reg.list()
