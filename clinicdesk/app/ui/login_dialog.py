from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.security.auth import AuthService


@dataclass(frozen=True)
class LoginOutcome:
    demo_mode: bool


LOGGER = get_logger(__name__)


class LoginDialog(QDialog):
    def __init__(self, auth_service: AuthService, i18n: I18nManager, *, demo_allowed: bool, parent=None) -> None:
        super().__init__(parent)
        self._auth_service = auth_service
        self._i18n = i18n
        self._demo_allowed = demo_allowed
        self.outcome = LoginOutcome(demo_mode=False)

        self._build_ui()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()

    def _build_ui(self) -> None:
        self.setModal(True)
        main_layout = QVBoxLayout(self)

        self.lbl_info = QLabel()
        self.lbl_info.setWordWrap(True)
        main_layout.addWidget(self.lbl_info)

        lang_row = QHBoxLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Español", "es")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self.lang_combo)
        main_layout.addLayout(lang_row)

        form = QFormLayout()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        form.addRow("", self.user_input)
        form.addRow("", self.pass_input)
        form.addRow("", self.confirm_input)
        main_layout.addLayout(form)
        self._form = form

        btn_row = QHBoxLayout()
        self.btn_login = QPushButton()
        self.btn_login.clicked.connect(self._on_login)
        self.btn_create = QPushButton()
        self.btn_create.clicked.connect(self._on_create)
        self.btn_demo = QPushButton()
        self.btn_demo.clicked.connect(self._on_demo)
        btn_row.addWidget(self.btn_login)
        btn_row.addWidget(self.btn_create)
        btn_row.addWidget(self.btn_demo)
        main_layout.addLayout(btn_row)

        self._refresh_mode()

    def _refresh_mode(self) -> None:
        first_run = not self._auth_service.has_users()
        self.confirm_input.setVisible(first_run)
        self.btn_create.setVisible(first_run)
        self.btn_login.setVisible(not first_run)
        self.btn_demo.setVisible(self._demo_allowed)

    def _on_language_changed(self) -> None:
        lang = self.lang_combo.currentData()
        self._i18n.set_language(lang)

    def _retranslate(self) -> None:
        self.setWindowTitle(self._i18n.t("login.title"))
        self.lbl_info.setText(self._i18n.t("login.first_run") if not self._auth_service.has_users() else "")
        self._form.setWidget(0, QFormLayout.LabelRole, QLabel(self._i18n.t("login.user")))
        self._form.setWidget(1, QFormLayout.LabelRole, QLabel(self._i18n.t("login.password")))
        self._form.setWidget(2, QFormLayout.LabelRole, QLabel(self._i18n.t("login.confirm_password")))
        self.btn_login.setText(self._i18n.t("login.submit"))
        self.btn_create.setText(self._i18n.t("login.create"))
        self.btn_demo.setText(self._i18n.t("login.demo"))

    def _on_create(self) -> None:
        username = self.user_input.text().strip()
        password = self.pass_input.text()
        confirm = self.confirm_input.text()
        if not username or not password:
            QMessageBox.warning(self, self.windowTitle(), self._i18n.t("login.error.required"))
            return
        if password != confirm:
            QMessageBox.warning(self, self.windowTitle(), self._i18n.t("login.error.mismatch"))
            return
        self._auth_service.create_user(username, password)
        QMessageBox.information(self, self.windowTitle(), self._i18n.t("login.ok.created"))
        self._refresh_mode()
        self._retranslate()

    def _on_login(self) -> None:
        username = self.user_input.text().strip()
        password = self.pass_input.text()
        if not username or not password:
            QMessageBox.warning(self, self.windowTitle(), self._i18n.t("login.error.required"))
            return
        result = self._auth_service.verify(username, password)
        if result.ok:
            LOGGER.info("auth_login_success")
            self.outcome = LoginOutcome(demo_mode=False)
            self.accept()
            return
        if result.locked:
            LOGGER.warning("auth_login_blocked")
        else:
            LOGGER.warning("auth_login_failed")
        error_key = "login.error.locked" if result.locked else "login.error.invalid"
        QMessageBox.warning(self, self.windowTitle(), self._i18n.t(error_key))

    def _on_demo(self) -> None:
        if not self._demo_allowed:
            QMessageBox.warning(self, self.windowTitle(), self._i18n.t("login.error.demo_disabled"))
            return
        LOGGER.warning("auth_login_demo_selected")
        self.outcome = LoginOutcome(demo_mode=True)
        self.accept()
