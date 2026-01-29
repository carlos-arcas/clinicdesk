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

    def list(self) -> List[PageDef]:
        # Orden estable por inserción
        return list(self._pages.values())


def get_pages(container: AppContainer) -> List[PageDef]:
    """Bootstrap UI: reúne todas las páginas registradas por feature."""
    reg = PageRegistry()
    register_pages(reg, container)
    return reg.list()
