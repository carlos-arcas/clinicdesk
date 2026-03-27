from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QWidget
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.ui import main_window as main_window_module
from clinicdesk.app.ui.main_window import MainWindow

pytestmark = [pytest.mark.ui, pytest.mark.uiqt, pytest.mark.integration]


class _PaginaPrueba(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.on_show_calls = 0

    def on_show(self) -> None:
        self.on_show_calls += 1


def test_on_csv_imported_refresca_pagina_ya_creada(monkeypatch: pytest.MonkeyPatch, qtbot, container) -> None:
    pagina_pacientes = _PaginaPrueba()
    monkeypatch.setattr(
        main_window_module,
        "get_pages",
        lambda *_args: [PageDef(key="pacientes", title="Pacientes", factory=lambda: pagina_pacientes)],
    )

    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None)
    qtbot.addWidget(window)

    assert pagina_pacientes.on_show_calls == 1

    window._on_csv_imported("Pacientes")

    assert pagina_pacientes.on_show_calls == 2


def test_on_csv_imported_no_crea_pagina_no_visitada(monkeypatch: pytest.MonkeyPatch, qtbot, container) -> None:
    pagina_pacientes = _PaginaPrueba()
    pagina_salas_creada = {"ok": False}

    def _crear_pagina_salas() -> QWidget:
        pagina_salas_creada["ok"] = True
        return _PaginaPrueba()

    monkeypatch.setattr(
        main_window_module,
        "get_pages",
        lambda *_args: [
            PageDef(key="pacientes", title="Pacientes", factory=lambda: pagina_pacientes),
            PageDef(key="salas", title="Salas", factory=_crear_pagina_salas),
        ],
    )

    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None)
    qtbot.addWidget(window)

    window._on_csv_imported("Salas")

    assert pagina_salas_creada["ok"] is False
