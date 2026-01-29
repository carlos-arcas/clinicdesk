# app/pages/page_nav_sidebar.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QVBoxLayout,
)

from app.pages.page_host import PageHost
from app.pages.page_registry import PageRegistry


class PageNavSidebar(QWidget):
    """
    Navegación por sidebar (lista vertical).
    """

    def __init__(self, registry: PageRegistry, host: PageHost) -> None:
        super().__init__()
        self._registry = registry
        self._host = host

        self._list = QListWidget()
        self._page_ids: list[str] = []

        for entry in self._registry.list_entries():
            item = QListWidgetItem(entry.title)
            self._list.addItem(item)
            self._page_ids.append(entry.page_id)

        self._list.currentRowChanged.connect(self._on_row_changed)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list)
        self.setLayout(layout)

    def _on_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._page_ids):
            self._host.show_page(self._page_ids[row])
