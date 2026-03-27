from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QWidget
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.main import _MainWindowFactory
from clinicdesk.app.pages.page_def import PageDef
from clinicdesk.app.session_controller import ContextoSesionAutenticada, ControladorSesionAutenticada
from clinicdesk.app.ui import main_window as main_window_module
from clinicdesk.app.ui.main_window import MainWindow

pytestmark = [pytest.mark.ui, pytest.mark.uiqt, pytest.mark.integration]


class _LoggerFalso:
    def __init__(self) -> None:
        self.eventos: list[str] = []

    def info(self, mensaje: str, extra=None) -> None:
        self.eventos.append(mensaje)

    def warning(self, mensaje: str, extra=None) -> None:
        self.eventos.append(mensaje)

    def error(self, mensaje: str, extra=None) -> None:
        self.eventos.append(mensaje)


class _PaginaMinima(QWidget):
    pass


def test_transicionar_post_login_abre_main_window_real(
    monkeypatch: pytest.MonkeyPatch,
    qtbot,
    qapp: QApplication,
    container,
) -> None:
    monkeypatch.setattr(
        main_window_module,
        "get_pages",
        lambda *_args: [PageDef(key="pacientes", title="Pacientes", factory=_PaginaMinima)],
    )
    i18n = I18nManager("es")
    logger = _LoggerFalso()
    errores: list[str] = []
    controlador = ControladorSesionAutenticada(
        app=qapp,
        i18n=i18n,
        logger=logger,
        factories=_MainWindowFactory(container, i18n),
        mostrar_error=errores.append,
    )

    ok = controlador.transicionar_post_login(
        ContextoSesionAutenticada(username="admin", demo_mode=False, run_id="run-login-ok"),
        lambda: None,
    )

    assert ok is True
    assert errores == []
    assert "post_login_transition_ok" in logger.eventos
    assert isinstance(controlador.ventana_principal, MainWindow)
    qtbot.addWidget(controlador.ventana_principal)
    qtbot.waitUntil(controlador.ventana_principal.isVisible)
    assert getattr(qapp, "ventana_principal") is controlador.ventana_principal
