from __future__ import annotations

from typing import Protocol

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class _I18nProtocol(Protocol):
    def t(self, key: str) -> str:
        ...


class PaginaBase(QWidget):
    def __init__(self, i18n: _I18nProtocol, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n

        self._layout_principal = QVBoxLayout(self)
        self._titulo = QLabel(self)
        self._descripcion = QLabel(self)
        self._layout_principal.addWidget(self._titulo)
        self._layout_principal.addWidget(self._descripcion)

        self._construir_widgets()
        self.actualizar_textos()

    def _construir_widgets(self) -> None:
        """Hook para que subclases construyan controles antes de actualizar textos."""

    def actualizar_textos(self) -> None:
        self._titulo.setText("")
        self._descripcion.setText("")
