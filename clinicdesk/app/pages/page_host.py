# app/pages/page_host.py
from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import QStackedWidget

from app.pages.base_page import BasePage
from app.pages.page_registry import PageRegistry


class PageHost(QStackedWidget):
    """
    Host de páginas (stack).

    - Crea pages lazy (la primera vez)
    - Permite cambiar por page_id
    """

    def __init__(self, registry: PageRegistry) -> None:
        super().__init__()
        self._registry = registry
        self._instances: Dict[str, BasePage] = {}

    def show_page(self, page_id: str) -> None:
        if page_id not in self._instances:
            entry = self._registry.get(page_id)
            page = entry.factory()
            self._instances[page_id] = page
            self.addWidget(page)

        page = self._instances[page_id]
        self.setCurrentWidget(page)
        page.on_show()
