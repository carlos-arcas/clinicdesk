from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PageHome(QWidget):
    """Home simple para navegación inicial."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("ClinicDesk")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Selecciona una sección en el menú lateral.")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(2)

    def on_show(self) -> None:
        pass
