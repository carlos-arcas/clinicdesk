from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QWidget,
)

from clinicdesk.app.application.csv.csv_service import CsvService
from clinicdesk.app.controllers.csv_controller import CsvController
from clinicdesk.app.application.preferencias.preferencias_usuario import PreferenciasUsuario
from clinicdesk.app.container import AppContainer
from clinicdesk.app.application.citas.navigation_intent import CitasNavigationIntentDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pages_registry import get_pages
from clinicdesk.app.ui.navigation_intent_store import IntentConsumible
from clinicdesk.app.ui.widgets.toast_manager import ToastManager, ToastPayload
from clinicdesk.app.ui.jobs.job_manager import JobManager, JobState
from clinicdesk.app.ui.lifecycle.controlador_cierre_app import ControladorCierreApp, DecisionCierre
from clinicdesk.app.ui.widgets.quick_search_dialog import ContextoBusquedaRapida, QuickSearchDialog


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
        "auditoria": "Audit",
        "gestion": "Management",
    },
}


class MainWindow(QMainWindow):
    def __init__(
        self,
        container: AppContainer,
        i18n: I18nManager,
        on_logout: Callable[[], None],
        shutdown_timeout_ms: int = 8_000,
    ) -> None:
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
        self._job_manager = JobManager(self)
        self._active_job_id: str | None = None
        self._job_toast_success_by_id: dict[str, str] = {}
        self._job_toast_fail_by_id: dict[str, str] = {}
        self._job_toast_cancel_by_id: dict[str, str] = {}
        self._job_success_cb_by_id: dict[str, Callable[[object], None]] = {}
        self._job_failed_cb_by_id: dict[str, Callable[[str], None]] = {}
        self._shutdown_timeout_ms = max(shutdown_timeout_ms, 0)
        self._controlador_cierre = ControladorCierreApp(timeout_ms=self._shutdown_timeout_ms)
        self._cierre_controlado_en_progreso = False
        self._permitir_cierre_directo = False
        self._shutdown_timeout_timer: QTimer | None = None

        for p in get_pages(container, self._i18n):
            self._factory_by_key[p.key] = p.factory
            item = QListWidgetItem(p.title)
            item.setData(Qt.UserRole, p.key)
            self.sidebar.addItem(item)
            self._sidebar_item_by_key[p.key] = item

        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        self._build_status_feedback()
        self._quick_search_dialog = QuickSearchDialog(self._i18n, self.container.preferencias_service, self)
        self._build_shortcuts()

        self._i18n.subscribe(self._retranslate)
        self._retranslate()
        self._restaurar_pagina_ultima()

    def _build_shortcuts(self) -> None:
        self._shortcut_busqueda = QShortcut(QKeySequence("Ctrl+K"), self)
        self._shortcut_busqueda.activated.connect(self._open_quick_search_for_current_page)
        self._shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        self._shortcut_refresh.activated.connect(self._refresh_current_page)
        self._shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        self._shortcut_new.activated.connect(self._new_on_current_page)

    def _current_page_key(self) -> str | None:
        row = self.sidebar.currentRow()
        if row < 0:
            return None
        item = self.sidebar.item(row)
        return item.data(Qt.UserRole)

    def _current_page_widget(self) -> QWidget | None:
        return self.stack.currentWidget()

    def actualizar_titulo_pagina(self, key: str, titulo: str) -> None:
        item = self._sidebar_item_by_key.get(key)
        if item is not None:
            item.setText(titulo)

    def _open_quick_search_for_current_page(self) -> None:
        key = self._current_page_key()
        page = self._current_page_widget()
        if key == "pacientes" and page is not None and hasattr(page, "buscar_rapido_async"):
            contexto = ContextoBusquedaRapida(
                contexto_id="pacientes",
                titulo_key="quick_search.title.pacientes",
                placeholder_key="quick_search.placeholder.pacientes",
                empty_key="quick_search.empty.pacientes",
                buscar_async=page.buscar_rapido_async,
                render_item=lambda paciente: paciente.nombre_completo,
                on_select=page.seleccionar_paciente_desde_busqueda,
            )
            self._quick_search_dialog.open_for(contexto)
            return
        if key == "confirmaciones" and page is not None and hasattr(page, "buscar_rapido_async"):
            contexto = ContextoBusquedaRapida(
                contexto_id="confirmaciones",
                titulo_key="quick_search.title.confirmaciones",
                placeholder_key="quick_search.placeholder.confirmaciones",
                empty_key="quick_search.empty.confirmaciones",
                buscar_async=page.buscar_rapido_async,
                render_item=lambda fila: f"{fila.inicio[:16]} · {fila.paciente} · {fila.estado_cita}",
                on_select=lambda fila: page.seleccionar_cita_desde_busqueda(fila.cita_id),
            )
            self._quick_search_dialog.open_for(contexto)

    def _refresh_current_page(self) -> None:
        page = self._current_page_widget()
        refresh = getattr(page, "refrescar_desde_atajo", None)
        if callable(refresh):
            refresh()

    def _new_on_current_page(self) -> None:
        page = self._current_page_widget()
        nuevo = getattr(page, "atajo_nuevo", None)
        if callable(nuevo):
            nuevo()

    def open_csv_dialog(self) -> None:
        self._csv_controller.open_dialog()

    def _crear_pagina_si_hace_falta(self, key: str) -> QWidget:
        indice = self._page_index_by_key.get(key)
        if indice is not None:
            widget = self.stack.widget(indice)
            assert widget is not None
            return widget
        factory = self._factory_by_key[key]
        widget = factory()
        indice = self.stack.addWidget(widget)
        self._page_index_by_key[key] = indice
        return widget

    def _guardar_pagina_actual(self, key: str) -> None:
        preferencias = self.container.preferencias_service.get()
        if preferencias.pagina_ultima == key:
            return
        self.container.preferencias_service.set(
            PreferenciasUsuario(
                pagina_ultima=key,
                restaurar_pagina_ultima_en_arranque=preferencias.restaurar_pagina_ultima_en_arranque,
                filtros_pacientes=preferencias.filtros_pacientes,
                filtros_confirmaciones=preferencias.filtros_confirmaciones,
                last_search_by_context=preferencias.last_search_by_context,
                columnas_por_contexto=preferencias.columnas_por_contexto,
            )
        )

    def _aplicar_intent_si_corresponde(self, key: str, widget: QWidget, intent: object | None) -> None:
        if key == "citas":
            if isinstance(intent, CitasNavigationIntentDTO):
                self._intent_citas.guardar(intent)
            intent = self._intent_citas.consumir()
        aplicar_intent = getattr(widget, "aplicar_intent", None)
        if intent is not None and callable(aplicar_intent):
            aplicar_intent(intent)

    def navigate(self, key: str, intent: object | None = None) -> QWidget | None:
        item = self._sidebar_item_by_key.get(key)
        if item is None:
            return None
        row = self.sidebar.row(item)
        self.sidebar.setCurrentRow(row)
        widget = self._crear_pagina_si_hace_falta(key)
        self._aplicar_intent_si_corresponde(key, widget, intent)
        return widget

    def _on_sidebar_changed(self, row: int) -> None:
        if row < 0:
            return
        item = self.sidebar.item(row)
        if item is None:
            return
        key = item.data(Qt.UserRole)
        actual = self.stack.currentWidget()
        if actual is not None and hasattr(actual, "on_hide"):
            actual.on_hide()
        widget = self._crear_pagina_si_hace_falta(key)
        self.stack.setCurrentWidget(widget)
        self._guardar_pagina_actual(key)
        on_show = getattr(widget, "on_show", None)
        if callable(on_show):
            on_show()

    def _restaurar_pagina_ultima(self) -> None:
        key = "pacientes"
        preferencias = self.container.preferencias_service.get()
        if preferencias.restaurar_pagina_ultima_en_arranque and preferencias.pagina_ultima:
            key = preferencias.pagina_ultima
        self.navigate(key)

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
        self._busy_indicator.setRange(0, 100)
        self._busy_indicator.setMaximumWidth(120)
        self._busy_indicator.hide()
        self._job_cancel_btn = QPushButton(self)
        self._job_cancel_btn.hide()
        self._job_cancel_btn.clicked.connect(self._on_cancel_active_job)
        self._status_bar.addPermanentWidget(self._busy_label)
        self._status_bar.addPermanentWidget(self._busy_indicator)
        self._status_bar.addPermanentWidget(self._job_cancel_btn)

        self._toast_close_btn = QPushButton(self)
        self._toast_close_btn.clicked.connect(self._close_toast)
        self._toast_titulo = QLabel(self)
        self._toast_titulo.setVisible(False)
        self._toast_label = QLabel(self)
        self._toast_accion_btn = QPushButton(self)
        self._toast_accion_btn.setVisible(False)
        self._toast_accion_btn.clicked.connect(self._run_toast_action)
        self._toast_detalles_btn = QPushButton(self)
        self._toast_detalles_btn.setVisible(False)
        self._toast_detalles_btn.clicked.connect(self._show_toast_details)
        self._toast_widget = QWidget(self)
        toast_layout = QHBoxLayout(self._toast_widget)
        toast_layout.setContentsMargins(8, 2, 8, 2)
        toast_layout.setSpacing(8)
        toast_layout.addWidget(self._toast_titulo)
        toast_layout.addWidget(self._toast_label)
        toast_layout.addWidget(self._toast_accion_btn)
        toast_layout.addWidget(self._toast_detalles_btn)
        toast_layout.addWidget(self._toast_close_btn)
        self._status_bar.addPermanentWidget(self._toast_widget)
        self._toast_widget.hide()

        self._toast_manager = ToastManager(
            traducir=self._i18n.t,
            programar=self._programar_toast,
            cancelar=self._cancelar_toast,
        )
        self._toast_manager.subscribe(self._render_toast)
        self._job_manager.started.connect(self._on_job_started)
        self._job_manager.progress.connect(self._on_job_progress)
        self._job_manager.finished.connect(self._on_job_finished)
        self._job_manager.failed.connect(self._on_job_failed)
        self._job_manager.cancelled.connect(self._on_job_cancelled)
        self._job_manager.cierre_seguro_completado.connect(self._on_cierre_seguro_completado)

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
        self._toast_accion_btn.setText(self._i18n.t("toast.action.default"))
        self._toast_detalles_btn.setText(self._i18n.t("toast.action.view_details"))
        self._job_cancel_btn.setText(self._i18n.t("job.cancel"))
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

    def _run_toast_action(self) -> None:
        self._toast_manager.run_current_action()

    def _show_toast_details(self) -> None:
        payload = self._toast_manager.actual
        if payload is None or not payload.tiene_detalle:
            return
        QMessageBox.information(
            self,
            payload.titulo or self._i18n.t("toast.details.title"),
            payload.detalle or "",
        )

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
        self._toast_titulo.setVisible(bool(payload.titulo))
        self._toast_titulo.setText(f"{payload.titulo}:" if payload.titulo else "")
        self._toast_label.setText(payload.mensaje)
        self._toast_accion_btn.setVisible(payload.tiene_accion)
        self._toast_accion_btn.setText(payload.accion_label or self._i18n.t("toast.action.default"))
        self._toast_detalles_btn.setVisible(payload.tiene_detalle)
        self._toast_widget.show()

    def toast_success(self, key: str, **kwargs: Any) -> None:
        self._toast_manager.success(key, **kwargs)

    def toast_info(self, key: str, **kwargs: Any) -> None:
        self._toast_manager.info(key, **kwargs)

    def toast_error(self, key: str, **kwargs: Any) -> None:
        self._toast_manager.error(key, **kwargs)

    def set_busy(self, busy: bool, mensaje_key: str) -> None:
        self._busy_key = mensaje_key if busy else None
        if busy:
            self._busy_indicator.show()
            self._busy_label.setText(self._i18n.t(mensaje_key))
            return
        self._busy_indicator.hide()
        self._busy_label.setText(self._i18n.t(self._busy_default_key))

    def run_premium_job(
        self,
        *,
        job_id: str,
        title_key: str,
        worker_factory,
        cancellable: bool,
        toast_success_key: str,
        toast_failed_key: str,
        toast_cancelled_key: str,
        on_success=None,
        on_failed=None,
    ) -> None:
        self._job_toast_success_by_id[job_id] = toast_success_key
        self._job_toast_fail_by_id[job_id] = toast_failed_key
        self._job_toast_cancel_by_id[job_id] = toast_cancelled_key
        if callable(on_success):
            self._job_success_cb_by_id[job_id] = on_success
        if callable(on_failed):
            self._job_failed_cb_by_id[job_id] = on_failed
        self._job_manager.run_job(job_id, title_key, worker_factory, cancellable=cancellable)

    def _on_job_started(self, state: JobState) -> None:
        self._active_job_id = state.id
        self._busy_indicator.show()
        self._busy_indicator.setValue(0)
        self._job_cancel_btn.setVisible(state.cancellable)
        self._busy_label.setText(self._format_job_status(state))

    def _on_job_progress(self, state: JobState) -> None:
        self._busy_indicator.setValue(state.progress)
        self._busy_label.setText(self._format_job_status(state))

    def _on_job_finished(self, state: JobState, result: object) -> None:
        self._reset_job_status()
        self.toast_success(self._job_toast_success_by_id.pop(state.id, "job.done"))
        self._job_toast_fail_by_id.pop(state.id, None)
        self._job_toast_cancel_by_id.pop(state.id, None)
        callback = self._job_success_cb_by_id.pop(state.id, None)
        self._job_failed_cb_by_id.pop(state.id, None)
        if callback is not None:
            callback(result)

    def _on_job_failed(self, state: JobState, error: str) -> None:
        self._reset_job_status()
        self.toast_error(self._job_toast_fail_by_id.pop(state.id, "job.failed"))
        self._job_toast_success_by_id.pop(state.id, None)
        self._job_toast_cancel_by_id.pop(state.id, None)
        self._job_success_cb_by_id.pop(state.id, None)
        callback = self._job_failed_cb_by_id.pop(state.id, None)
        if callback is not None:
            callback(error)

    def _on_job_cancelled(self, state: JobState) -> None:
        self._reset_job_status()
        self.toast_info(self._job_toast_cancel_by_id.pop(state.id, "job.cancelled"))
        self._job_toast_success_by_id.pop(state.id, None)
        self._job_toast_fail_by_id.pop(state.id, None)
        self._job_success_cb_by_id.pop(state.id, None)
        self._job_failed_cb_by_id.pop(state.id, None)

    def _on_cancel_active_job(self) -> None:
        if self._active_job_id is None:
            return
        self._job_manager.cancel_job(self._active_job_id)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        decision = self._controlador_cierre.solicitar_cierre(ids_jobs_activos=self._job_manager.ids_jobs_activos())
        self._sincronizar_estado_cierre()
        if decision.permitir_cierre:
            super().closeEvent(event)
            return
        if decision.iniciar_shutdown:
            self._iniciar_cierre_controlado()
            event.ignore()
            return
        if decision.ignorar_evento:
            event.ignore()
            return
        super().closeEvent(event)

    def _iniciar_cierre_controlado(self) -> None:
        self.sidebar.setEnabled(False)
        self._job_cancel_btn.setEnabled(False)
        self._busy_indicator.show()
        self._busy_indicator.setValue(0)
        self._busy_label.setText(self._i18n.t("job.shutdown.status"))
        self.toast_info("job.shutdown.requested")
        self._job_manager.solicitar_cierre_seguro()
        self._armar_timeout_cierre()

    def _armar_timeout_cierre(self) -> None:
        if self._shutdown_timeout_timer is not None:
            return
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(self._on_shutdown_timeout)
        timer.start(self._shutdown_timeout_ms)
        self._shutdown_timeout_timer = timer

    def _cancelar_timeout_cierre(self) -> None:
        if self._shutdown_timeout_timer is None:
            return
        self._shutdown_timeout_timer.stop()
        self._shutdown_timeout_timer.deleteLater()
        self._shutdown_timeout_timer = None

    def _on_shutdown_timeout(self) -> None:
        decision = self._controlador_cierre.intentar_timeout(ids_jobs_activos=self._job_manager.ids_jobs_activos())
        self._shutdown_timeout_timer = None
        self._aplicar_timeout_si_corresponde(decision)

    def _aplicar_timeout_si_corresponde(self, decision: DecisionCierre) -> None:
        if not decision.restaurar_estado_ui:
            return
        self.sidebar.setEnabled(True)
        self._job_cancel_btn.setEnabled(True)
        self._busy_indicator.hide()
        self._busy_label.setText(self._i18n.t(self._busy_default_key))
        if decision.toast_key is not None:
            self.toast_error(decision.toast_key)
        self._sincronizar_estado_cierre()

    def _on_cierre_seguro_completado(self) -> None:
        self._cancelar_timeout_cierre()
        decision = self._controlador_cierre.registrar_cierre_completado()
        self._sincronizar_estado_cierre()
        if decision.completar_cierre:
            self.close()

    def _sincronizar_estado_cierre(self) -> None:
        self._cierre_controlado_en_progreso = self._controlador_cierre.cierre_en_progreso
        self._permitir_cierre_directo = self._controlador_cierre.permitir_cierre_directo

    def _reset_job_status(self) -> None:
        self._active_job_id = None
        self._busy_indicator.hide()
        self._job_cancel_btn.hide()
        if self._cierre_controlado_en_progreso:
            self._busy_indicator.show()
            self._busy_label.setText(self._i18n.t("job.shutdown.status"))
            return
        self._busy_label.setText(self._i18n.t(self._busy_default_key))

    def _format_job_status(self, state: JobState) -> str:
        return self._i18n.t("job.status.pattern").format(
            title=self._i18n.t(state.title_key),
            progress=state.progress,
            message=self._i18n.t(state.message_key),
        )
