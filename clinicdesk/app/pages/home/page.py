from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.gestion.page import PageGestionDashboard


class PageHome(QWidget):
    """Home operativa reutilizando el dashboard de gestión."""

    def __init__(self, container: AppContainer, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._page_gestion = PageGestionDashboard(container=container, i18n=i18n, parent=self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._page_gestion)

    def on_show(self) -> None:
        self._page_gestion.on_show()
