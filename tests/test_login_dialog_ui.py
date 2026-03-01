from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    from PySide6.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover - depende de librerías del sistema
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.security.auth import AuthService
from clinicdesk.app.ui.login_dialog import LoginDialog


@pytest.fixture(scope="session")
def qapp() -> Iterator[QApplication]:
    app = QApplication.instance() or QApplication([])
    yield app


def _build_auth_service() -> AuthService:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    return AuthService(connection)


def test_login_dialog_no_duplica_celdas_en_retranslate(qapp: QApplication) -> None:
    del qapp
    mensajes_qt: list[str] = []
    dialogo = None

    def _handler(_msg_type: QtMsgType, _context, message: str) -> None:
        mensajes_qt.append(message)

    previo = qInstallMessageHandler(_handler)
    try:
        dialogo = LoginDialog(_build_auth_service(), I18nManager("es"), demo_allowed=True)
        dialogo.show()
        dialogo._on_language_changed()
        dialogo._i18n.set_language("en")
        dialogo._i18n.set_language("es")
    finally:
        qInstallMessageHandler(previo)
        if dialogo is not None:
            dialogo.close()

    assert not [m for m in mensajes_qt if "QFormLayoutPrivate::setItem" in m and "already occupied" in m]


def test_botones_login_y_demo_responden(qapp: QApplication) -> None:
    del qapp
    auth_service = _build_auth_service()
    auth_service.create_user("admin", "secret123")

    dialogo_login = LoginDialog(auth_service, I18nManager("es"), demo_allowed=True)
    dialogo_login.user_input.setText("admin")
    dialogo_login.pass_input.setText("secret123")

    dialogo_login.btn_login.click()

    assert dialogo_login.result() == dialogo_login.Accepted
    assert dialogo_login.outcome.demo_mode is False

    dialogo_demo = LoginDialog(auth_service, I18nManager("es"), demo_allowed=True)
    dialogo_demo.btn_demo.click()

    assert dialogo_demo.result() == dialogo_demo.Accepted
    assert dialogo_demo.outcome.demo_mode is True

    dialogo_login.close()
    dialogo_demo.close()
