from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.security import Role
from clinicdesk.app.i18n import I18nManager

try:
    from clinicdesk.app.pages.citas.page import PageCitas
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PageCitas no disponible en este entorno: {exc}", allow_module_level=True)

pytestmark = [pytest.mark.ui, pytest.mark.uiqt]


class _ControllerSpy:
    def __init__(self, resultado: bool = False) -> None:
        self.calls: list[str] = []
        self.resultado = resultado

    def create_cita_flow(self, fecha: str) -> bool:
        self.calls.append(fecha)
        return self.resultado


def test_page_citas_readonly_muestra_bloqueo_visible_y_no_dispara_creacion(qtbot, container) -> None:
    container.user_context.role = Role.READONLY
    page = PageCitas(container, I18nManager("es"))
    page._controller = _ControllerSpy(resultado=True)
    qtbot.addWidget(page)

    assert page._can_write is False
    assert page.btn_new.isEnabled() is False

    qtbot.mouseClick(page.btn_new, Qt.LeftButton)
    page._on_new()

    assert page._controller.calls == []


def test_page_citas_admin_habilita_boton_y_delega_en_controller(qtbot, container) -> None:
    container.user_context.role = Role.ADMIN
    page = PageCitas(container, I18nManager("es"))
    page._controller = _ControllerSpy(resultado=False)
    qtbot.addWidget(page)

    assert page._can_write is True
    assert page.btn_new.isEnabled() is True

    page._on_new()

    assert len(page._controller.calls) == 1
    assert page._controller.calls[0].count("-") == 2
