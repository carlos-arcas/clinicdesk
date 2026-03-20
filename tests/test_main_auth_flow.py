from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QDialog, QWidget
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.main import abrir_sesion_autenticada
from clinicdesk.app.security.auth import AuthService
from clinicdesk.app.session_controller import ContextoSesionAutenticada, ControladorSesionAutenticada
from clinicdesk.app.ui.login_dialog import LoginOutcome
from tests.conftest import _apply_pragmas, _apply_schema, _ensure_test_migrations

pytestmark = [pytest.mark.ui, pytest.mark.uiqt, pytest.mark.integration]


@pytest.fixture()
def auth_service_temporal(tmp_path: Path) -> AuthService:
    sqlite_path = tmp_path / "auth-flow.sqlite"
    connection = sqlite3.connect(sqlite_path.as_posix())
    connection.row_factory = sqlite3.Row
    _apply_pragmas(connection)
    _apply_schema(connection)
    _ensure_test_migrations(connection)
    auth_service = AuthService(connection)
    auth_service.create_user("admin", "secret123")
    try:
        yield auth_service
    finally:
        connection.close()


class LoggerFalso:
    def __init__(self) -> None:
        self.eventos: list[tuple[str, dict[str, str] | None]] = []

    def info(self, mensaje: str, extra=None) -> None:
        self.eventos.append((mensaje, extra))

    def warning(self, mensaje: str, extra=None) -> None:
        self.eventos.append((mensaje, extra))

    def error(self, mensaje: str, extra=None) -> None:
        self.eventos.append((mensaje, extra))


class VentanaPrincipalPrueba(QWidget):
    def __init__(self, contexto: ContextoSesionAutenticada, on_logout) -> None:
        super().__init__()
        self.contexto = contexto
        self._on_logout = on_logout
        self.hide_count = 0
        self.close_count = 0

    def hide(self) -> None:
        self.hide_count += 1
        super().hide()

    def close(self) -> bool:
        self.close_count += 1
        return super().close()

    def ejecutar_logout(self) -> None:
        self._on_logout()


class FabricaVentanaSecuencial:
    def __init__(self, fallar_en_indices: set[int] | None = None) -> None:
        self._fallar_en_indices = fallar_en_indices or set()
        self.contextos: list[ContextoSesionAutenticada] = []
        self.ventanas: list[VentanaPrincipalPrueba] = []

    def crear_ventana_principal(self, contexto: ContextoSesionAutenticada, on_logout):
        indice = len(self.contextos)
        self.contextos.append(contexto)
        if indice in self._fallar_en_indices:
            return None
        ventana = VentanaPrincipalPrueba(contexto, on_logout)
        self.ventanas.append(ventana)
        return ventana


class DialogoLoginProgramado:
    def __init__(self, resultado: int, outcome: LoginOutcome | None = None) -> None:
        self._resultado = resultado
        self.outcome = outcome or LoginOutcome(demo_mode=False, username="")

    def exec(self) -> int:
        return self._resultado


class CreadorDialogosProgramados:
    def __init__(self, respuestas: list[DialogoLoginProgramado]) -> None:
        self._respuestas = list(respuestas)
        self.invocaciones = 0

    def __call__(self, auth: AuthService, i18n: I18nManager, demo_allowed: bool) -> DialogoLoginProgramado:
        assert auth.verify("admin", "secret123").ok is True
        assert i18n.t("login.title")
        assert demo_allowed is True
        if not self._respuestas:
            raise AssertionError("No hay más respuestas programadas para LoginDialog")
        self.invocaciones += 1
        return self._respuestas.pop(0)


def _crear_controlador(app: QApplication, fabrica: FabricaVentanaSecuencial, errores: list[str], logger: LoggerFalso):
    return ControladorSesionAutenticada(
        app=app,
        i18n=I18nManager("es"),
        logger=logger,
        factories=fabrica,
        mostrar_error=errores.append,
    )


def test_flujo_autenticacion_reabre_sesion_tras_logout(qtbot, qapp: QApplication, auth_service_temporal: AuthService) -> None:
    logger = LoggerFalso()
    errores: list[str] = []
    fabrica = FabricaVentanaSecuencial()
    controlador = _crear_controlador(qapp, fabrica, errores, logger)
    dialogos = CreadorDialogosProgramados(
        [
            DialogoLoginProgramado(QDialog.Accepted, LoginOutcome(demo_mode=False, username="admin")),
            DialogoLoginProgramado(QDialog.Accepted, LoginOutcome(demo_mode=True, username="demo")),
        ]
    )

    ok = abrir_sesion_autenticada(
        app=qapp,
        auth=auth_service_temporal,
        i18n=I18nManager("es"),
        demo_allowed=True,
        controlador=controlador,
        run_id="run-auth-e2e",
        crear_dialogo_login=dialogos,
    )

    assert ok is True
    primera_ventana = fabrica.ventanas[0]
    qtbot.addWidget(primera_ventana)
    qtbot.waitUntil(primera_ventana.isVisible)
    assert primera_ventana.contexto.username == "admin"

    primera_ventana.ejecutar_logout()

    assert dialogos.invocaciones == 2
    assert len(fabrica.ventanas) == 2
    segunda_ventana = fabrica.ventanas[1]
    qtbot.addWidget(segunda_ventana)
    qtbot.waitUntil(segunda_ventana.isVisible)
    assert primera_ventana.isVisible() is False
    assert primera_ventana.close_count >= 1
    assert segunda_ventana.contexto.username == "demo"
    assert segunda_ventana.contexto.demo_mode is True
    assert controlador.ventana_principal is segunda_ventana
    assert getattr(qapp, "ventana_principal") is segunda_ventana
    assert errores == []


def test_logout_con_cancelacion_cierra_widgets_superiores(qtbot, qapp: QApplication, auth_service_temporal: AuthService) -> None:
    logger = LoggerFalso()
    errores: list[str] = []
    fabrica = FabricaVentanaSecuencial()
    controlador = _crear_controlador(qapp, fabrica, errores, logger)
    dialogos = CreadorDialogosProgramados(
        [
            DialogoLoginProgramado(QDialog.Accepted, LoginOutcome(demo_mode=False, username="admin")),
            DialogoLoginProgramado(QDialog.Rejected),
        ]
    )

    ok = abrir_sesion_autenticada(
        app=qapp,
        auth=auth_service_temporal,
        i18n=I18nManager("es"),
        demo_allowed=True,
        controlador=controlador,
        run_id="run-auth-cancel",
        crear_dialogo_login=dialogos,
    )

    assert ok is True
    ventana = fabrica.ventanas[0]
    qtbot.addWidget(ventana)
    qtbot.waitUntil(ventana.isVisible)

    ventana.ejecutar_logout()

    qtbot.waitUntil(lambda: not any(widget.isVisible() for widget in qapp.topLevelWidgets()))
    assert qapp.quitOnLastWindowClosed() is True
    assert ventana.close_count >= 1
    assert errores == []


def test_error_post_login_muestra_feedback_y_no_cierra_widgets_ajenos(
    qtbot,
    qapp: QApplication,
    auth_service_temporal: AuthService,
) -> None:
    logger = LoggerFalso()
    errores: list[str] = []
    fabrica = FabricaVentanaSecuencial(fallar_en_indices={0})
    controlador = _crear_controlador(qapp, fabrica, errores, logger)
    dialogos = CreadorDialogosProgramados(
        [
            DialogoLoginProgramado(QDialog.Accepted, LoginOutcome(demo_mode=False, username="admin")),
            DialogoLoginProgramado(QDialog.Rejected),
        ]
    )
    widget_ajeno = QWidget()
    qtbot.addWidget(widget_ajeno)
    widget_ajeno.show()
    qtbot.waitUntil(widget_ajeno.isVisible)

    ok = abrir_sesion_autenticada(
        app=qapp,
        auth=auth_service_temporal,
        i18n=I18nManager("es"),
        demo_allowed=True,
        controlador=controlador,
        run_id="run-auth-error",
        crear_dialogo_login=dialogos,
    )

    assert ok is False
    assert errores == ["session.error.open_failed"]
    assert widget_ajeno.isVisible() is True
    assert controlador.ventana_principal is None
    assert any(evento[0] == "post_login_transition_fail" for evento in logger.eventos)
    assert any(
        evento == (
            "post_login_transition_fail",
            {
                "action": "post_login_transition_fail",
                "reason_code": "dependency_wiring_failed",
                "exc_type": "none",
            },
        )
        for evento in logger.eventos
    )
