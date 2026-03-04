from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QWidget,
)

from clinicdesk.app.application.csv.csv_service import CsvService
from clinicdesk.app.controllers.csv_controller import CsvController
from clinicdesk.app.container import AppContainer
from clinicdesk.app.application.citas.navigation_intent import CitasNavigationIntentDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pages_registry import get_pages
from clinicdesk.app.ui.vistas.main_window import state_controller, validacion_preventiva
from clinicdesk.app.ui.navigation_intent_store import IntentConsumible
from clinicdesk.app.ui.widgets.toast_manager import ToastManager, ToastPayload


_PAGE_TITLES_BY_LANG = {
    "es": {
        "home": "Inicio",
        "pacientes": "Pacientes",
        "citas": "Citas",
        "medicos": "Médicos",
        "personal": "Personal",
        "salas": "Salas",
        "farmacia": "Farmacia",
        "medicamentos": "Medicamentos",
        "materiales": "Materiales",
        "recetas": "Recetas",
        "dispensaciones": "Dispensaciones",
        "turnos": "Turnos",
        "ausencias": "Ausencias",
        "incidencias": "Incidencias",
        "demo_ml": "Demo ML",
        "auditoria": "Auditoría",
        "gestion": "Gestión",
    },
    "en": {
        "home": "Home",
        "pacientes": "Patients",
        "citas": "Appointments",
        "medicos": "Doctors",
        "personal": "Staff",
        "salas": "Rooms",
        "farmacia": "Pharmacy",
        "medicamentos": "Medicines",
        "materiales": "Supplies",
        "recetas": "Prescriptions",
        "dispensaciones": "Dispensations",
        "turnos": "Shifts",
        "ausencias": "Absences",
        "incidencias": "Incidents",
        "demo_ml": "ML Demo",
        "auditoria": "Audit",
        "gestion": "Management",
    },
}


class MainWindow(QMainWindow):
    def __init__(self, container: AppContainer, i18n: I18nManager, on_logout: Callable[[], None]) -> None:
        super().__init__()
        self.container = container
        self._i18n = i18n
        self._on_logout_callback = on_logout
        self._csv_controller = CsvController(
            self,
            CsvService(container),
            on_import_complete=self._on_csv_imported,
        )

        self.resize(1200, 800)

        root = QWidget()
        self.setCentralWidget(root)

        self._build_menu()

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setSelectionMode(QListWidget.SingleSelection)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)

        self._page_index_by_key: Dict[str, int] = {}
        self._factory_by_key: Dict[str, Callable[[], QWidget]] = {}
        self._sidebar_item_by_key: Dict[str, QListWidgetItem] = {}
        self._intent_citas = IntentConsumible[CitasNavigationIntentDTO]()
        self._busy_key: str | None = None
        self._busy_default_key = "status.ready"

        for p in get_pages(container, self._i18n):
            self._factory_by_key[p.key] = p.factory
            item = QListWidgetItem(p.title)
            item.setData(Qt.UserRole, p.key)
            self.sidebar.addItem(item)
            self._sidebar_item_by_key[p.key] = item

        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        self._build_status_feedback()

        self._i18n.subscribe(self._retranslate)
        self._retranslate()
        self.navigate("home")

    def open_csv_dialog(self) -> None:
        self._csv_controller.open_dialog()

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        self.menu_archivo = menu_bar.addMenu("")

        self.action_csv = QAction("", self)
        self.action_csv.triggered.connect(self._csv_controller.open_dialog)

        self.action_logout = QAction("", self)
        self.action_logout.triggered.connect(self._on_logout_callback)

        self.action_exit = QAction("", self)
        self.action_exit.triggered.connect(self.close)

        self.menu_language = menu_bar.addMenu("")
        self.action_lang_es = QAction("", self)
        self.action_lang_es.triggered.connect(lambda: self._i18n.set_language("es"))
        self.action_lang_en = QAction("", self)
        self.action_lang_en.triggered.connect(lambda: self._i18n.set_language("en"))

        self.menu_archivo.addAction(self.action_csv)
        self.menu_archivo.addAction(self.action_logout)
        self.menu_archivo.addSeparator()
        self.menu_archivo.addAction(self.action_exit)

        self.menu_language.addAction(self.action_lang_es)
        self.menu_language.addAction(self.action_lang_en)

    def _build_status_feedback(self) -> None:
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)

        self._busy_label = QLabel(self)
        self._busy_indicator = QProgressBar(self)
        self._busy_indicator.setRange(0, 0)
        self._busy_indicator.setMaximumWidth(120)
        self._busy_indicator.hide()
        self._status_bar.addPermanentWidget(self._busy_label)
        self._status_bar.addPermanentWidget(self._busy_indicator)

        self._toast_close_btn = QPushButton(self)
        self._toast_close_btn.clicked.connect(self._close_toast)
        self._toast_label = QLabel(self)
        self._toast_widget = QWidget(self)
        toast_layout = QHBoxLayout(self._toast_widget)
        toast_layout.setContentsMargins(8, 2, 8, 2)
        toast_layout.setSpacing(8)
        toast_layout.addWidget(self._toast_label)
        toast_layout.addWidget(self._toast_close_btn)
        self._status_bar.addPermanentWidget(self._toast_widget)
        self._toast_widget.hide()

        self._toast_manager = ToastManager(
            traducir=self._i18n.t,
            programar=self._programar_toast,
            cancelar=self._cancelar_toast,
        )
        self._toast_manager.subscribe(self._render_toast)

    def _retranslate(self) -> None:
        self.setWindowTitle(self._i18n.t("app.title"))
        self.menu_archivo.setTitle(self._i18n.t("menu.file"))
        self.action_csv.setText(self._i18n.t("menu.csv"))
        self.action_logout.setText(self._i18n.t("menu.logout"))
        self.action_exit.setText(self._i18n.t("menu.exit"))
        self.menu_language.setTitle(self._i18n.t("menu.language"))
        self.action_lang_es.setText(self._i18n.t("lang.es"))
        self.action_lang_en.setText(self._i18n.t("lang.en"))

        labels = _PAGE_TITLES_BY_LANG.get(self._i18n.language, _PAGE_TITLES_BY_LANG["es"])
        for key, item in self._sidebar_item_by_key.items():
            if key == "prediccion_ausencias":
                item.setText(self._i18n.t("nav.prediccion_ausencias"))
                continue
            if key == "confirmaciones":
                item.setText(self._i18n.t("nav.confirmaciones"))
                continue
            item.setText(labels.get(key, item.text()))

        self._toast_close_btn.setText(self._i18n.t("comun.cerrar"))
        if self._busy_key is None:
            self._busy_label.setText(self._i18n.t(self._busy_default_key))
        else:
            self._busy_label.setText(self._i18n.t(self._busy_key))

    def _programar_toast(self, delay_ms: int, callback: Callable[[], None]) -> QTimer:
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        timer.start(delay_ms)
        return timer

    def _cancelar_toast(self, timer: QTimer) -> None:
        timer.stop()
        timer.deleteLater()

    def _close_toast(self) -> None:
        self._toast_manager.close_current()

    def _render_toast(self, payload: ToastPayload | None) -> None:
        if payload is None:
            self._toast_widget.hide()
            return
        estilo = {
            "success": "background:#0f5132;color:#ffffff;border-radius:4px;",
            "info": "background:#055160;color:#ffffff;border-radius:4px;",
            "error": "background:#842029;color:#ffffff;border-radius:4px;",
        }.get(payload.tipo, "")
        self._toast_widget.setStyleSheet(estilo)
        self._toast_label.setText(payload.mensaje)
        self._toast_widget.show()

    def toast_success(self, key: str) -> None:
        self._toast_manager.success(key)

    def toast_info(self, key: str) -> None:
        self._toast_manager.info(key)

    def toast_error(self, key: str) -> None:
        self._toast_manager.error(key)

    def set_busy(self, busy: bool, mensaje_key: str) -> None:
        self._busy_key = mensaje_key if busy else None
        if busy:
            self._busy_indicator.show()
            self._busy_label.setText(self._i18n.t(mensaje_key))
            return
        self._busy_indicator.hide()
        self._busy_label.setText(self._i18n.t(self._busy_default_key))

    def _on_csv_imported(self, entity: str) -> None:
        key_by_entity = {
            "Pacientes": "pacientes",
            "Médicos": "medicos",
            "Personal": "personal",
            "Medicamentos": "medicamentos",
            "Materiales": "materiales",
            "Salas": "salas",
        }
        key = key_by_entity.get(entity)
        if not key:
            return
        index = self._page_index_by_key.get(key)
        if index is None:
            return
        widget = self.stack.widget(index)
        if widget is not None and hasattr(widget, "on_show"):
            widget.on_show()

    def _ensure_page_created(self, key: str) -> Optional[int]:
        if key in self._page_index_by_key:
            return self._page_index_by_key[key]

        factory = self._factory_by_key.get(key)
        if factory is None:
            return None

        widget = factory()
        index = self.stack.addWidget(widget)
        self._page_index_by_key[key] = index
        return index

    def _call_on_hide_current(self) -> None:
        w = self.stack.currentWidget()
        if w is not None and hasattr(w, "on_hide"):
            w.on_hide()

    def _call_on_show_index(self, index: int) -> None:
        w = self.stack.widget(index)
        if w is not None and hasattr(w, "on_show"):
            w.on_show()

    def navigate(self, key: str, intent: Any | None = None) -> None:
        self.sidebar.blockSignals(True)
        try:
            self._call_on_hide_current()

            index = self._ensure_page_created(key)
            if index is None:
                return

            self.stack.setCurrentIndex(index)
            self._call_on_show_index(index)
            self._aplicar_intent_navegacion(key, intent)

            for row in range(self.sidebar.count()):
                it = self.sidebar.item(row)
                if it.data(Qt.UserRole) == key:
                    self.sidebar.setCurrentRow(row)
                    break
        finally:
            self.sidebar.blockSignals(False)

    def _aplicar_intent_navegacion(self, key: str, intent: Any | None) -> None:
        if key != "citas":
            return
        if isinstance(intent, CitasNavigationIntentDTO):
            self._intent_citas.guardar(intent)
        cita_intent = self._intent_citas.consumir()
        if cita_intent is None:
            return
        pagina = self.stack.currentWidget()
        if pagina is not None and hasattr(pagina, "aplicar_intent"):
            pagina.aplicar_intent(cita_intent)

    def _on_sidebar_changed(self, row: int) -> None:
        if row < 0:
            return

        self._call_on_hide_current()

        item = self.sidebar.item(row)
        key = item.data(Qt.UserRole)

        index = self._ensure_page_created(key)
        if index is None:
            return

        self.stack.setCurrentIndex(index)
        self._call_on_show_index(index)
        self._aplicar_intent_navegacion(key, None)

    def _normalize_input_heights(self) -> None:
        state_controller._normalize_input_heights(self)

    def _bind_preventive_validation_events(self) -> None:
        validacion_preventiva._bind_preventive_validation_events(self)

    def _mark_field_touched(self, field_name: str) -> None:
        validacion_preventiva._mark_field_touched(self, field_name)

    def _schedule_preventive_validation(self) -> None:
        validacion_preventiva._schedule_preventive_validation(self)

    def _run_preventive_validation(self):
        return validacion_preventiva._run_preventive_validation(self)

    def _collect_base_preventive_errors(self):
        return validacion_preventiva._collect_base_preventive_errors(self)

    def _collect_preventive_validation(self):
        return validacion_preventiva._collect_preventive_validation(self)

    def _collect_preventive_business_rules(self):
        return validacion_preventiva._collect_preventive_business_rules(self)

    def _collect_pending_duplicates_warning(self):
        return validacion_preventiva._collect_pending_duplicates_warning(self)

    def _on_go_to_existing_duplicate(self) -> None:
        validacion_preventiva._on_go_to_existing_duplicate(self)

    def _render_preventive_validation(self, result) -> None:
        validacion_preventiva._render_preventive_validation(self, result)

    def _run_preconfirm_checks(self) -> bool:
        return validacion_preventiva._run_preconfirm_checks(self)

    def closeEvent(self, event):
        self.container.close()
        event.accept()
