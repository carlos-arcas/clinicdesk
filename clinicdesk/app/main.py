from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog

from clinicdesk.app.bootstrap import bootstrap_database, resolve_db_path
from clinicdesk.app.bootstrap_logging import configure_logging, get_logger, set_run_context
from clinicdesk.app.container import build_container
from clinicdesk.app.crash_handler import install_global_exception_hook
from clinicdesk.app.i18n import I18nManager
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


def main() -> int:
    configure_logging("clinicdesk-ui", Path("./logs"), level="INFO", json=True)
    set_run_context(uuid.uuid4().hex[:8])
    install_global_exception_hook(LOGGER)
    _install_ui_log_buffer()

    app = QApplication(sys.argv)
    app.setStyleSheet(load_qss())

    con = bootstrap_database(apply_schema=True)
    container = build_container(con)
    i18n = I18nManager("es")
    auth = AuthService(con)

    db_path = resolve_db_path(emit_log=False)
    demo_allowed = is_demo_mode_allowed(db_path)

    current_window: MainWindow | None = None

    def open_authenticated_session() -> bool:
        nonlocal current_window
        login = LoginDialog(auth, i18n, demo_allowed=demo_allowed)
        if login.exec() != QDialog.Accepted:
            return False

        if login.outcome.demo_mode:
            LOGGER.warning("auth_mode=DEMO access_granted")
        else:
            LOGGER.info("auth_mode=STANDARD access_granted")

        if current_window is not None:
            current_window.close()

        def _logout() -> None:
            LOGGER.info("session_logout")
            if current_window is not None:
                current_window.hide()
            if not open_authenticated_session():
                app.quit()

        current_window = MainWindow(container, i18n=i18n, on_logout=_logout)
        current_window.show()
        return True

    if not open_authenticated_session():
        container.close()
        return 0

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
