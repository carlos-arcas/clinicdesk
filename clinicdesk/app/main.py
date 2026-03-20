from __future__ import annotations

import logging
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from clinicdesk.app.bootstrap import bootstrap_database, resolve_db_path
from clinicdesk.app.bootstrap_logging import configure_logging, get_logger, set_run_context
from clinicdesk.app.container import build_container
from clinicdesk.app.crash_handler import install_global_exception_hook
from clinicdesk.app.infrastructure.crash_logger import instalar_hooks_crash
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.security.auth import AuthService, is_demo_mode_allowed
from clinicdesk.app.session_controller import (
    ContextoSesionAutenticada,
    ControladorSesionAutenticada,
    FabricaVentanaPrincipal,
)
from clinicdesk.app.ui.log_buffer_handler import LogBufferHandler
from clinicdesk.app.ui.login_dialog import LoginDialog, LoginOutcome
from clinicdesk.app.ui.main_window import MainWindow
from clinicdesk.app.ui.theme import load_qss


LOGGER = get_logger(__name__)


class _UIRunIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = "-"
        return True


class DialogoLoginEjecutable(Protocol):
    outcome: LoginOutcome

    def exec(self) -> int: ...


class FabricaDialogoLogin(Protocol):
    def __call__(self, auth: AuthService, i18n: I18nManager, demo_allowed: bool) -> DialogoLoginEjecutable: ...


@dataclass(frozen=True, slots=True)
class ContextoEntrypointDesktop:
    app: QApplication
    container: Any
    i18n: I18nManager
    auth: AuthService
    controlador: ControladorSesionAutenticada
    run_id: str
    demo_allowed: bool

    @property
    def ventana_principal(self) -> Any | None:
        return self.controlador.ventana_principal


class PreparadorLoopEntrypoint(Protocol):
    def __call__(self, contexto: ContextoEntrypointDesktop) -> None: ...


def _ejecutar_loop_qt(app: QApplication) -> int:
    return app.exec()


def _install_ui_log_buffer() -> LogBufferHandler:
    handler = LogBufferHandler(capacity=300)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(run_id)s] %(name)s %(message)s")
    handler.setFormatter(formatter)
    handler.addFilter(_UIRunIdFilter())
    logging.getLogger().addHandler(handler)
    return handler


class _MainWindowFactory(FabricaVentanaPrincipal):
    def __init__(self, container, i18n: I18nManager) -> None:
        self._container = container
        self._i18n = i18n

    def crear_ventana_principal(self, contexto: ContextoSesionAutenticada, on_logout):
        self._container.user_context.demo_mode = contexto.demo_mode
        self._container.user_context.username = contexto.username
        self._container.user_context.run_id = contexto.run_id
        return MainWindow(self._container, i18n=self._i18n, on_logout=on_logout)


def _log_about_to_quit(app: QApplication) -> None:
    top_levels = list(app.topLevelWidgets())
    visible_top_levels = [widget for widget in top_levels if widget.isVisible()]
    LOGGER.info(
        "app_about_to_quit",
        extra={
            "action": "app_about_to_quit",
            "top_level_count": len(top_levels),
            "visible_top_level_count": len(visible_top_levels),
            "reason_code": "unknown",
        },
    )


def _inicializar_app() -> tuple[QApplication, str]:
    instalar_hooks_crash(Path("./logs"))
    configure_logging("clinicdesk-ui", Path("./logs"), level="INFO", json=True)
    run_id = uuid.uuid4().hex[:8]
    set_run_context(run_id)
    install_global_exception_hook(LOGGER)
    _install_ui_log_buffer()
    app = QApplication.instance() or QApplication(sys.argv)
    app.aboutToQuit.connect(lambda: _log_about_to_quit(app))
    app.setStyleSheet(load_qss())
    return app, run_id


def _crear_controlador_sesion(app: QApplication, container, i18n: I18nManager) -> ControladorSesionAutenticada:
    main_window_factory = _MainWindowFactory(container, i18n)

    def _mostrar_error_transicion(mensaje: str) -> None:
        QMessageBox.warning(None, i18n.t("login.title"), mensaje)

    return ControladorSesionAutenticada(
        app=app,
        i18n=i18n,
        logger=LOGGER,
        factories=main_window_factory,
        mostrar_error=_mostrar_error_transicion,
    )


def _crear_dialogo_login(auth: AuthService, i18n: I18nManager, demo_allowed: bool) -> DialogoLoginEjecutable:
    return LoginDialog(auth, i18n, demo_allowed=demo_allowed)


@dataclass(frozen=True, slots=True)
class ControlEntrypointDesktop:
    crear_dialogo_login: FabricaDialogoLogin = _crear_dialogo_login
    preparar_loop: PreparadorLoopEntrypoint | None = None
    ejecutar_loop: Callable[[QApplication], int] = _ejecutar_loop_qt


def _cerrar_widgets_superiores(app: QApplication) -> None:
    app.setQuitOnLastWindowClosed(True)
    for widget in list(app.topLevelWidgets()):
        widget.close()
        widget.deleteLater()
    app.processEvents()


def _crear_callback_logout(
    app: QApplication,
    auth: AuthService,
    i18n: I18nManager,
    demo_allowed: bool,
    controlador: ControladorSesionAutenticada,
    run_id: str,
    crear_dialogo_login: FabricaDialogoLogin,
) -> Callable[[], None]:
    def _logout() -> None:
        LOGGER.info("session_logout")
        if controlador.ventana_principal is not None:
            controlador.ventana_principal.hide()
        if not abrir_sesion_autenticada(
            app=app,
            auth=auth,
            i18n=i18n,
            demo_allowed=demo_allowed,
            controlador=controlador,
            run_id=run_id,
            crear_dialogo_login=crear_dialogo_login,
        ):
            _cerrar_widgets_superiores(app)

    return _logout


def abrir_sesion_autenticada(
    *,
    app: QApplication,
    auth: AuthService,
    i18n: I18nManager,
    demo_allowed: bool,
    controlador: ControladorSesionAutenticada,
    run_id: str,
    crear_dialogo_login: FabricaDialogoLogin = _crear_dialogo_login,
) -> bool:
    while True:
        app.setQuitOnLastWindowClosed(False)
        login = crear_dialogo_login(auth, i18n, demo_allowed)
        if login.exec() != QDialog.Accepted:
            return False

        if login.outcome.demo_mode:
            LOGGER.warning("auth_mode=DEMO access_granted")
        else:
            LOGGER.info("auth_mode=STANDARD access_granted")

        contexto = ContextoSesionAutenticada(
            username=login.outcome.username,
            demo_mode=login.outcome.demo_mode,
            run_id=run_id,
        )
        logout = _crear_callback_logout(app, auth, i18n, demo_allowed, controlador, run_id, crear_dialogo_login)
        if controlador.transicionar_post_login(contexto, logout):
            return True
        LOGGER.error(
            "post_login_transition_fail",
            extra={
                "action": "post_login_transition_fail",
                "reason_code": "dependency_wiring_failed",
                "exc_type": "none",
            },
        )


def main(control: ControlEntrypointDesktop | None = None) -> int:
    control = control or ControlEntrypointDesktop()
    app, run_id = _inicializar_app()

    con = bootstrap_database(apply_schema=True)
    container = build_container(con)
    i18n = I18nManager("es")
    auth = AuthService(con)

    db_path = resolve_db_path(emit_log=False)
    demo_allowed = is_demo_mode_allowed(db_path)
    controlador = _crear_controlador_sesion(app=app, container=container, i18n=i18n)

    if not abrir_sesion_autenticada(
        app=app,
        auth=auth,
        i18n=i18n,
        demo_allowed=demo_allowed,
        controlador=controlador,
        run_id=run_id,
        crear_dialogo_login=control.crear_dialogo_login,
    ):
        container.close()
        return 0

    contexto = ContextoEntrypointDesktop(
        app=app,
        container=container,
        i18n=i18n,
        auth=auth,
        controlador=controlador,
        run_id=run_id,
        demo_allowed=demo_allowed,
    )
    if control.preparar_loop is not None:
        control.preparar_loop(contexto)

    try:
        return control.ejecutar_loop(app)
    finally:
        _cerrar_widgets_superiores(app)
        container.close()


if __name__ == "__main__":
    raise SystemExit(main())
