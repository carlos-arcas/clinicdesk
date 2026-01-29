# app/pages/base_page.py
from __future__ import annotations

from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget


class BasePage(QWidget, ABC):
    """
    Base común para todas las páginas.
    """

    @property
    @abstractmethod
    def page_id(self) -> str:
        ...

    @property
    @abstractmethod
    def title(self) -> str:
        ...

    def on_show(self) -> None:
        """
        Hook opcional: se llama cuando la página se muestra.
        """
        return
