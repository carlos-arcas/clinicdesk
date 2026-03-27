from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.ui import main_window as main_window_module
from clinicdesk.app.ui.main_window import MainWindow

pytestmark = [pytest.mark.ui, pytest.mark.uiqt]


class _PaginaAlta(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(2200)
        layout = QVBoxLayout(self)
        for indice in range(40):
            layout.addWidget(QLabel(f"Fila {indice}", self))


def test_main_window_muestra_scroll_vertical_si_pagina_excede_viewport(
    qtbot, container, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        main_window_module,
        "get_pages",
        lambda *_args: [PageDef(key="pacientes", title="Pacientes", factory=_PaginaAlta)],
    )

    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None)
    qtbot.addWidget(window)
    window.resize(800, 500)
    window.show()

    qtbot.waitUntil(lambda: isinstance(window.stack.currentWidget(), _PaginaAlta))
    qtbot.waitUntil(lambda: window._stack_scroll.verticalScrollBar().maximum() > 0)

    assert window.stack.currentWidget() is not None
