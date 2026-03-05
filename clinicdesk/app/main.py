from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from clinicdesk.app.bootstrap import bootstrap_database, resolve_db_path
from clinicdesk.app.bootstrap_logging import configure_logging, get_logger, set_run_context
from clinicdesk.app.container import build_container
from clinicdesk.app.crash_handler import install_global_exception_hook
from clinicdesk.app.infrastructure.crash_logger import instalar_hooks_crash
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.session_controller import (
    ContextoSesionAutenticada,
    ControladorSesionAutenticada,
    FabricaVentanaPrincipal,
)
from clinicdesk.app.security.auth import AuthService, is_demo_mode_allowed
from clinicdesk.app.ui.log_buffer_handler import LogBufferHandler
from clinicdesk.app.ui.login_dialog import LoginDialog
from clinicdesk.app.ui.main_window import MainWindow
from clinicdesk.app.ui.theme import load_qss


LOGGER = get_logger(__name__)


class _UIRunIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = "-"
        return True


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


def main() -> int:
    instalar_hooks_crash(Path("./logs"))
    configure_logging("clinicdesk-ui", Path("./logs"), level="INFO", json=True)
    run_id = uuid.uuid4().hex[:8]
    set_run_context(run_id)
    install_global_exception_hook(LOGGER)
    _install_ui_log_buffer()

    app = QApplication(sys.argv)
    app.aboutToQuit.connect(lambda: _log_about_to_quit(app))
    app.setStyleSheet(load_qss())

    con = bootstrap_database(apply_schema=True)
    container = build_container(con)
    i18n = I18nManager("es")
    auth = AuthService(con)

    db_path = resolve_db_path(emit_log=False)
    demo_allowed = is_demo_mode_allowed(db_path)

    main_window_factory = _MainWindowFactory(container, i18n)

    def _mostrar_error_transicion(mensaje: str) -> None:
        QMessageBox.warning(None, i18n.t("login.title"), mensaje)

    controlador = ControladorSesionAutenticada(
        app=app,
        i18n=i18n,
        logger=LOGGER,
        factories=main_window_factory,
        mostrar_error=_mostrar_error_transicion,
    )

    def open_authenticated_session() -> bool:
        while True:
            app.setQuitOnLastWindowClosed(False)
            login = LoginDialog(auth, i18n, demo_allowed=demo_allowed)
            if login.exec() != QDialog.Accepted:
                return False

            if login.outcome.demo_mode:
                LOGGER.warning("auth_mode=DEMO access_granted")
            else:
                LOGGER.info("auth_mode=STANDARD access_granted")

            def _logout() -> None:
                LOGGER.info("session_logout")
                if controlador.ventana_principal is not None:
                    controlador.ventana_principal.hide()
                if not open_authenticated_session():
                    app.setQuitOnLastWindowClosed(True)
                    for widget in app.topLevelWidgets():
                        widget.close()

            contexto = ContextoSesionAutenticada(
                username=login.outcome.username,
                demo_mode=login.outcome.demo_mode,
                run_id=run_id,
            )
            if controlador.transicionar_post_login(contexto, _logout):
                return True
            LOGGER.error(
                "post_login_transition_fail",
                extra={
                    "action": "post_login_transition_fail",
                    "reason_code": "dependency_wiring_failed",
                    "exc_type": "none",
                },
            )

    if not open_authenticated_session():
        container.close()
        return 0

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
