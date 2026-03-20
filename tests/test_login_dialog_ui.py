from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    from PySide6.QtWidgets import QApplication, QMessageBox
except ImportError as exc:  # pragma: no cover - depende de librerías del sistema
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.security.auth import AuthService
from clinicdesk.app.ui.login_dialog import LoginDialog


@pytest.fixture(scope="session")
def qapp() -> Iterator[QApplication]:
    app = QApplication.instance() or QApplication([])
    yield app


def _build_auth_service(*, now_provider=None, max_attempts: int = 5, lock_seconds: int = 60) -> AuthService:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    return AuthService(
        connection,
        max_attempts=max_attempts,
        lock_seconds=lock_seconds,
        now_provider=now_provider,
    )


@pytest.fixture
def capturador_mensajes(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    mensajes: list[tuple[str, str, str]] = []

    def _capturar_warning(_parent, titulo: str, texto: str):
        mensajes.append(("warning", titulo, texto))
        return QMessageBox.Ok

    def _capturar_information(_parent, titulo: str, texto: str):
        mensajes.append(("information", titulo, texto))
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "warning", _capturar_warning)
    monkeypatch.setattr(QMessageBox, "information", _capturar_information)
    return mensajes


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


def test_first_run_crea_usuario_y_cambia_a_modo_login(qtbot, capturador_mensajes) -> None:
    auth_service = _build_auth_service()
    dialogo = LoginDialog(auth_service, I18nManager("es"), demo_allowed=True)
    qtbot.addWidget(dialogo)

    assert auth_service.has_users() is False
    assert dialogo.confirm_input.isVisible() is True
    assert dialogo.btn_create.isVisible() is True
    assert dialogo.btn_login.isVisible() is False

    dialogo.user_input.setText("admin")
    dialogo.pass_input.setText("secret123")
    dialogo.confirm_input.setText("secret123")

    dialogo.btn_create.click()

    assert auth_service.has_users() is True
    assert dialogo.confirm_input.isVisible() is False
    assert dialogo.btn_create.isVisible() is False
    assert dialogo.btn_login.isVisible() is True
    assert capturador_mensajes == [("information", dialogo.windowTitle(), dialogo._i18n.t("login.ok.created"))]

    dialogo.close()


@pytest.mark.parametrize(
    ("username", "password", "confirmacion", "clave_esperada"),
    [
        ("", "", "", "login.error.required"),
        ("admin", "secret123", "otra", "login.error.mismatch"),
    ],
)
def test_first_run_valida_datos_invalidos(
    qtbot,
    capturador_mensajes,
    username: str,
    password: str,
    confirmacion: str,
    clave_esperada: str,
) -> None:
    auth_service = _build_auth_service()
    dialogo = LoginDialog(auth_service, I18nManager("es"), demo_allowed=True)
    qtbot.addWidget(dialogo)

    dialogo.user_input.setText(username)
    dialogo.pass_input.setText(password)
    dialogo.confirm_input.setText(confirmacion)

    dialogo.btn_create.click()

    assert auth_service.has_users() is False
    assert capturador_mensajes == [("warning", dialogo.windowTitle(), dialogo._i18n.t(clave_esperada))]


def test_login_valido_acepta_y_expone_outcome(qtbot, capturador_mensajes) -> None:
    auth_service = _build_auth_service()
    auth_service.create_user("admin", "secret123")
    dialogo = LoginDialog(auth_service, I18nManager("es"), demo_allowed=True)
    qtbot.addWidget(dialogo)

    dialogo.user_input.setText("admin")
    dialogo.pass_input.setText("secret123")

    dialogo.btn_login.click()

    assert dialogo.result() == dialogo.Accepted
    assert dialogo.outcome.demo_mode is False
    assert dialogo.outcome.username == "admin"
    assert capturador_mensajes == []


def test_login_invalido_hasta_bloqueo_muestra_feedback_correcto(qtbot, capturador_mensajes) -> None:
    reloj = {"ahora": datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)}
    auth_service = _build_auth_service(
        now_provider=lambda: reloj["ahora"],
        max_attempts=2,
        lock_seconds=120,
    )
    auth_service.create_user("admin", "secret123")
    dialogo = LoginDialog(auth_service, I18nManager("es"), demo_allowed=True)
    qtbot.addWidget(dialogo)
    dialogo.user_input.setText("admin")

    dialogo.pass_input.setText("bad-1")
    dialogo.btn_login.click()
    dialogo.pass_input.setText("bad-2")
    dialogo.btn_login.click()
    dialogo.pass_input.setText("secret123")
    dialogo.btn_login.click()

    assert [mensaje[2] for mensaje in capturador_mensajes] == [
        dialogo._i18n.t("login.error.invalid"),
        dialogo._i18n.t("login.error.locked"),
        dialogo._i18n.t("login.error.locked"),
    ]
    assert auth_service.verify("admin", "secret123").locked is True

    reloj["ahora"] += timedelta(seconds=121)

    assert auth_service.verify("admin", "secret123").ok is True


def test_demo_mode_permitido_acepta_dialogo(qtbot, capturador_mensajes) -> None:
    auth_service = _build_auth_service()
    auth_service.create_user("admin", "secret123")
    dialogo = LoginDialog(auth_service, I18nManager("es"), demo_allowed=True)
    qtbot.addWidget(dialogo)

    dialogo.btn_demo.click()

    assert dialogo.result() == dialogo.Accepted
    assert dialogo.outcome == dialogo.outcome.__class__(demo_mode=True, username="demo")
    assert capturador_mensajes == []


def test_demo_mode_prohibido_rechaza_con_feedback(qtbot, capturador_mensajes) -> None:
    auth_service = _build_auth_service()
    auth_service.create_user("admin", "secret123")
    dialogo = LoginDialog(auth_service, I18nManager("es"), demo_allowed=False)
    qtbot.addWidget(dialogo)

    dialogo._on_demo()

    assert dialogo.result() == dialogo.Rejected
    assert dialogo.outcome.demo_mode is False
    assert capturador_mensajes == [("warning", dialogo.windowTitle(), dialogo._i18n.t("login.error.demo_disabled"))]
