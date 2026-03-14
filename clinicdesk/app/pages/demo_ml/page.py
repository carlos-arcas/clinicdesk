from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QDate, QObject, QSettings, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.ml.drift_explain import explain_drift
from clinicdesk.app.application.ml.interpretacion_ml_humana import (
    interpretar_drift,
    interpretar_entrenamiento,
    interpretar_scoring,
)
from clinicdesk.app.application.ml.lecturas_operativas_ml import (
    LecturaOperativaML,
    construir_lectura_operativa_drift,
    construir_lectura_operativa_exportacion,
    construir_lectura_operativa_metricas,
    construir_lectura_operativa_scoring,
)
from clinicdesk.app.application.services.analytics_workflow_service import (
    AnalyticsWorkflowConfig,
    AnalyticsWorkflowResult,
    AnalyticsWorkflowService,
)
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.priorizacion_operativa_ml_service import (
    ListaTrabajoML,
    NivelPrioridadML,
    PriorizacionOperativaMLService,
)
from clinicdesk.app.application.services.ml_centro_guiado_service import CentroMLGuiadoService
from clinicdesk.app.application.services.ml_playbook_ejecucion_service import (
    AccionPlaybookEjecutable,
    ContextoEjecucionPlaybook,
    PlaybookEjecucionService,
    ResultadoPasoPlaybook,
)
from clinicdesk.app.application.services.demo_run_service import CancelToken
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest
from clinicdesk.app.bootstrap_logging import get_logger, set_run_context
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui.widgets.kpi_card import KpiCard
from clinicdesk.app.ui.widgets.progress_dialog import ProgressDialog

LOGGER = get_logger(__name__)


class _TaskWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, run_id: str, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn
        self._run_id = run_id

    def run(self) -> None:
        set_run_context(self._run_id)
        try:
            self.finished.emit(self._fn())
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class _WorkflowWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        run_id: str,
        workflow: AnalyticsWorkflowService,
        from_date: str,
        to_date: str,
        config: AnalyticsWorkflowConfig,
        previous_dataset_version: str | None,
        seed_request: SeedDemoDataRequest | None,
        cancel_token: CancelToken | None,
    ) -> None:
        super().__init__()
        self._run_id = run_id
        self._workflow = workflow
        self._from_date = from_date
        self._to_date = to_date
        self._config = config
        self._previous_dataset_version = previous_dataset_version
        self._seed_request = seed_request
        self._cancel_token = cancel_token

    def run(self) -> None:
        set_run_context(self._run_id)
        try:
            result = self._workflow.run_full_workflow(
                self._from_date,
                self._to_date,
                self._config,
                previous_dataset_version=self._previous_dataset_version,
                seed_request=self._seed_request,
                cancel_token=self._cancel_token,
                progress_callback=self._emit_progress,
            )
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))

    def _emit_progress(self, percent: int, message: str) -> None:
        self.progress.emit(percent, message)


class PageDemoML(QWidget):
    _STEPS = [
        "Preparar datos para análisis",
        "Crear modelo de predicción",
        "Analizar citas y estimar riesgo",
        "Detectar cambios en comportamiento",
    ]

    def __init__(self, facade: DemoMLFacade, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._facade = facade
        self._i18n = i18n
        self._workflow = AnalyticsWorkflowService(facade)
        self._centro_service = CentroMLGuiadoService(facade)
        self._playbook_ejecucion = PlaybookEjecucionService(facade)
        self._priorizacion_service = PriorizacionOperativaMLService()
        self._settings = QSettings("clinicdesk", "analytics_demo")
        self._thread: QThread | None = None
        self._workflow_worker: _WorkflowWorker | None = None
        self._cancel_token: CancelToken | None = None
        self._run_id = ""
        self._last_result: AnalyticsWorkflowResult | None = None
        self._last_train: Any | None = None
        self._last_score: Any | None = None
        self._last_drift: Any | None = None
        self._playbook_seleccionado = ""
        self._accion_playbook_actual: AccionPlaybookEjecutable | None = None
        self._ultimo_resultado_playbook: ResultadoPasoPlaybook | None = None
        self._lista_trabajo_ml: ListaTrabajoML | None = None
        self._build_ui()

    def _t(self, key: str) -> str:
        return self._i18n.t(key)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.addWidget(self._build_left_column())
        splitter.addWidget(self._build_right_column())
        splitter.setSizes([650, 550])
        root.addWidget(splitter)
        self._restore_settings()
        self._refresh_tables()
        self._reset_kpi_cards()
        self._refresh_guided_state()

    def _build_left_column(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(self._build_seed_panel())
        layout.addWidget(self._build_tables())
        return panel

    def _build_right_column(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(self._build_kpi_panel())
        layout.addWidget(self._build_workflow_panel())
        layout.addWidget(self._build_recomendaciones_panel())
        layout.addWidget(self._build_lectura_operativa_panel())
        layout.addWidget(self._build_lista_trabajo_panel())
        layout.addWidget(self._build_playbook_panel())
        layout.addWidget(self._build_resumen_ejecutivo_panel())
        layout.addWidget(self._build_advanced_panel())
        layout.addWidget(QLabel("Resumen de actividad"))
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        layout.addWidget(self.txt_logs)
        return panel

    def _build_kpi_panel(self) -> QWidget:
        box = QGroupBox("Resumen rápido")
        row = QHBoxLayout(box)
        self.card_citas = KpiCard("Citas analizadas")
        self.card_risk = KpiCard("Riesgo alto")
        self.card_threshold = KpiCard("Threshold aplicado")
        self.card_drift = KpiCard("Drift")
        for card in [self.card_citas, self.card_risk, self.card_threshold, self.card_drift]:
            row.addWidget(card)
        return box

    def _build_seed_panel(self) -> QWidget:
        box = QGroupBox("Datos demo")
        form = QFormLayout(box)
        self.seed_seed = QSpinBox()
        self.seed_seed.setRange(1, 999999)
        self.seed_seed.setValue(123)
        self.seed_doctors = QSpinBox()
        self.seed_doctors.setRange(1, 300)
        self.seed_doctors.setValue(10)
        self.seed_patients = QSpinBox()
        self.seed_patients.setRange(1, 2000)
        self.seed_patients.setValue(80)
        self.seed_appointments = QSpinBox()
        self.seed_appointments.setRange(1, 10000)
        self.seed_appointments.setValue(300)
        self.seed_from = QDateEdit()
        self.seed_from.setCalendarPopup(True)
        self.seed_from.setDate(QDate.currentDate().addDays(-30))
        self.seed_to = QDateEdit()
        self.seed_to.setCalendarPopup(True)
        self.seed_to.setDate(QDate.currentDate())
        self.seed_incidence = QLineEdit("0.15")
        form.addRow("Semilla", self.seed_seed)
        form.addRow("Médicos", self.seed_doctors)
        form.addRow("Pacientes", self.seed_patients)
        form.addRow("Citas", self.seed_appointments)
        form.addRow("Desde", self.seed_from)
        form.addRow("Hasta", self.seed_to)
        form.addRow("Incidencia", self.seed_incidence)
        return box

    def _build_workflow_panel(self) -> QWidget:
        box = QGroupBox("Analítica (Demo)")
        form = QFormLayout(box)
        self.chk_seed_full = QCheckBox("Generar datos demo si faltan")
        self.chk_seed_full.setChecked(True)
        self.score_limit = QSpinBox()
        self.score_limit.setRange(1, 10000)
        self.score_limit.setValue(20)
        self.export_dir = QLineEdit(self._settings.value("last_export_dir", "./exports", str) or "./exports")
        self.lbl_last = QLabel("Último análisis: sin ejecuciones")
        self.lbl_estado = QLabel(self._t("demo_ml.estado.pipeline_pendiente"))
        self.lbl_estado.setWordWrap(True)
        self.lbl_recomendado = QLabel(self._t("demo_ml.estado.siguiente.prepare"))
        self.lbl_recomendado.setWordWrap(True)
        self.lbl_export_files = QLabel("Archivos exportados: aún no hay resultados")
        self.lbl_export_files.setWordWrap(True)
        self.btn_open_export = QPushButton("Abrir carpeta de exportación")
        self.btn_open_export.clicked.connect(self._open_export_folder)
        self.btn_full = QPushButton("Ejecutar demo completa")
        self.btn_full.clicked.connect(self._run_full_workflow)
        cards = QHBoxLayout()
        self.btn_prepare = QPushButton("1) Preparar datos para análisis")
        self.btn_train = QPushButton("2) Crear modelo de predicción")
        self.btn_score = QPushButton("3) Analizar citas y estimar riesgo")
        self.btn_drift = QPushButton("4) Detectar cambios en comportamiento")
        self.btn_prepare.clicked.connect(self._run_prepare)
        self.btn_train.clicked.connect(self._run_train)
        self.btn_score.clicked.connect(self._run_score)
        self.btn_drift.clicked.connect(self._run_drift)
        for btn in [self.btn_prepare, self.btn_train, self.btn_score, self.btn_drift]:
            cards.addWidget(btn)
        form.addRow(self.btn_full)
        form.addRow(self.chk_seed_full)
        form.addRow("Límite de riesgo", self.score_limit)
        form.addRow("Exportar para Power BI", self.export_dir)
        form.addRow(cards)
        form.addRow(self.btn_open_export)
        form.addRow(self.lbl_export_files)
        form.addRow(self.lbl_estado)
        form.addRow(self.lbl_recomendado)
        form.addRow(self.lbl_last)
        return box

    def _build_recomendaciones_panel(self) -> QWidget:
        box = QGroupBox(self._t("demo_ml.asistente.panel.titulo"))
        form = QFormLayout(box)
        self.lbl_reco_principal = QLabel(self._t("demo_ml.asistente.panel.vacio"))
        self.lbl_reco_principal.setWordWrap(True)
        self.lbl_reco_secundarias = QLabel(self._t("demo_ml.asistente.panel.vacio"))
        self.lbl_reco_secundarias.setWordWrap(True)
        self.lbl_reco_advertencias = QLabel(self._t("demo_ml.asistente.panel.vacio"))
        self.lbl_reco_advertencias.setWordWrap(True)
        form.addRow(self._t("demo_ml.asistente.panel.principal"), self.lbl_reco_principal)
        form.addRow(self._t("demo_ml.asistente.panel.secundarias"), self.lbl_reco_secundarias)
        form.addRow(self._t("demo_ml.asistente.panel.advertencias"), self.lbl_reco_advertencias)
        return box



    def _build_lectura_operativa_panel(self) -> QWidget:
        box = QGroupBox(self._t("demo_ml.operativa.panel.titulo"))
        form = QFormLayout(box)
        self.lbl_operativa_semaforo = QLabel(self._t("demo_ml.operativa.panel.vacio"))
        self.lbl_operativa_significado = QLabel(self._t("demo_ml.operativa.panel.vacio"))
        self.lbl_operativa_utilidad = QLabel(self._t("demo_ml.operativa.panel.vacio"))
        self.lbl_operativa_accion = QLabel(self._t("demo_ml.operativa.panel.vacio"))
        self.lbl_operativa_no_concluir = QLabel(self._t("demo_ml.operativa.panel.vacio"))
        for widget in (
            self.lbl_operativa_semaforo,
            self.lbl_operativa_significado,
            self.lbl_operativa_utilidad,
            self.lbl_operativa_accion,
            self.lbl_operativa_no_concluir,
        ):
            widget.setWordWrap(True)
        form.addRow(self._t("demo_ml.operativa.panel.semaforo"), self.lbl_operativa_semaforo)
        form.addRow(self._t("demo_ml.operativa.panel.que_dice"), self.lbl_operativa_significado)
        form.addRow(self._t("demo_ml.operativa.panel.para_que"), self.lbl_operativa_utilidad)
        form.addRow(self._t("demo_ml.operativa.panel.que_haria"), self.lbl_operativa_accion)
        form.addRow(self._t("demo_ml.operativa.panel.que_no_concluir"), self.lbl_operativa_no_concluir)
        return box

    def _build_playbook_panel(self) -> QWidget:
        box = QGroupBox(self._t("demo_ml.playbook.panel.titulo"))
        form = QFormLayout(box)
        self.cmb_playbook = QComboBox()
        self.cmb_playbook.currentIndexChanged.connect(self._on_playbook_changed)
        self.lbl_playbook_resumen = QLabel(self._t("demo_ml.playbook.panel.vacio"))
        self.lbl_playbook_resumen.setWordWrap(True)
        self.lbl_playbook_pasos = QLabel(self._t("demo_ml.playbook.panel.vacio"))
        self.lbl_playbook_pasos.setWordWrap(True)
        self.lbl_playbook_siguiente = QLabel(self._t("demo_ml.playbook.panel.vacio"))
        self.lbl_playbook_siguiente.setWordWrap(True)
        self.lbl_playbook_progreso = QLabel(self._t("demo_ml.playbook.panel.vacio"))
        self.lbl_playbook_progreso.setWordWrap(True)
        self.lbl_playbook_resultado = QLabel(self._t("demo_ml.playbook.panel.vacio"))
        self.lbl_playbook_resultado.setWordWrap(True)
        self.btn_playbook_cta = QPushButton(self._t("demo_ml.playbook.ejecucion.cta.sin_accion"))
        self.btn_playbook_cta.clicked.connect(self._run_playbook_action)
        form.addRow(self._t("demo_ml.playbook.panel.objetivo"), self.cmb_playbook)
        form.addRow(self._t("demo_ml.playbook.panel.resumen"), self.lbl_playbook_resumen)
        form.addRow(self._t("demo_ml.playbook.panel.siguiente"), self.lbl_playbook_siguiente)
        form.addRow(self._t("demo_ml.playbook.panel.progreso"), self.lbl_playbook_progreso)
        form.addRow(self._t("demo_ml.playbook.panel.ultimo_resultado"), self.lbl_playbook_resultado)
        form.addRow(self._t("demo_ml.playbook.panel.accion"), self.btn_playbook_cta)
        form.addRow(self._t("demo_ml.playbook.panel.pasos"), self.lbl_playbook_pasos)
        return box

    def _build_lista_trabajo_panel(self) -> QWidget:
        box = QGroupBox(self._t("demo_ml.priorizacion.panel.titulo"))
        form = QFormLayout(box)
        self.lbl_priorizacion_resumen = QLabel(self._t("demo_ml.priorizacion.panel.vacio"))
        self.lbl_priorizacion_resumen.setWordWrap(True)
        self.cmb_priorizacion_filtro = QComboBox()
        self.cmb_priorizacion_filtro.currentIndexChanged.connect(self._render_lista_trabajo_ml)
        self.cmb_priorizacion_filtro.addItem(self._t("demo_ml.priorizacion.filtro.todos"), "todos")
        self.cmb_priorizacion_filtro.addItem(self._t("demo_ml.priorizacion.filtro.alta"), NivelPrioridadML.ALTA.value)
        self.cmb_priorizacion_filtro.addItem(self._t("demo_ml.priorizacion.filtro.media"), NivelPrioridadML.MEDIA.value)
        self.cmb_priorizacion_filtro.addItem(self._t("demo_ml.priorizacion.filtro.baja"), NivelPrioridadML.BAJA.value)
        self.tbl_priorizacion_ml = self._mk_table(
            [
                self._t("demo_ml.priorizacion.columna.cita"),
                self._t("demo_ml.priorizacion.columna.prioridad"),
                self._t("demo_ml.priorizacion.columna.accion"),
                self._t("demo_ml.priorizacion.columna.motivo"),
                self._t("demo_ml.priorizacion.columna.cautela"),
            ]
        )
        form.addRow(self._t("demo_ml.priorizacion.panel.resumen"), self.lbl_priorizacion_resumen)
        form.addRow(self._t("demo_ml.priorizacion.panel.filtro"), self.cmb_priorizacion_filtro)
        form.addRow(self.tbl_priorizacion_ml)
        return box

    def _build_resumen_ejecutivo_panel(self) -> QWidget:
        box = QGroupBox(self._t("demo_ml.resumen.panel.titulo"))
        form = QFormLayout(box)
        self.lbl_resumen_estado = QLabel()
        self.lbl_resumen_falta = QLabel()
        self.lbl_resumen_paso = QLabel()
        self.lbl_resumen_riesgo = QLabel()
        self.lbl_resumen_utilidad = QLabel()
        for lbl in [
            self.lbl_resumen_estado,
            self.lbl_resumen_falta,
            self.lbl_resumen_paso,
            self.lbl_resumen_riesgo,
            self.lbl_resumen_utilidad,
        ]:
            lbl.setWordWrap(True)
        form.addRow(self._t("demo_ml.resumen.estado_actual"), self.lbl_resumen_estado)
        form.addRow(self._t("demo_ml.resumen.que_falta"), self.lbl_resumen_falta)
        form.addRow(self._t("demo_ml.resumen.siguiente_paso"), self.lbl_resumen_paso)
        form.addRow(self._t("demo_ml.resumen.riesgo"), self.lbl_resumen_riesgo)
        form.addRow(self._t("demo_ml.resumen.utilidad"), self.lbl_resumen_utilidad)
        return box

    def _build_advanced_panel(self) -> QWidget:
        box = QGroupBox("Avanzado")
        box.setCheckable(True)
        box.setChecked(False)
        form = QFormLayout(box)
        self.adv_dataset = QLineEdit()
        self.adv_model = QLineEdit()
        self.adv_prev_dataset = QLineEdit()
        self.adv_summary = QTextEdit()
        self.adv_summary.setReadOnly(True)
        form.addRow("dataset_version", self.adv_dataset)
        form.addRow("model_version", self.adv_model)
        form.addRow("dataset_version previo", self.adv_prev_dataset)
        form.addRow("Resumen", self.adv_summary)
        return box

    def _build_tables(self) -> QWidget:
        self.tabs = QTabWidget()
        self.tbl_doctors = self._mk_table(["ID", "Documento", "Nombre", "Tel", "Especialidad", "Activo"])
        self.tbl_patients = self._mk_table(["ID", "Documento", "Nombre", "Tel", "Activo"])
        self.tbl_appointments = self._mk_table(["ID", "Inicio", "Fin", "Paciente", "Médico", "Estado", "Motivo"])
        self.tbl_incidences = self._mk_table(["ID", "Fecha", "Tipo", "Severidad", "Estado", "Descripción"])
        self.tabs.addTab(self.tbl_doctors, "Médicos")
        self.tabs.addTab(self.tbl_patients, "Pacientes")
        self.tabs.addTab(self.tbl_appointments, "Citas")
        self.tabs.addTab(self.tbl_incidences, "Incidencias")
        return self.tabs

    def _mk_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _run_prepare(self) -> None:
        fn = lambda: self._workflow.prepare_analysis(self._from(), self._to(), self.adv_dataset.text().strip() or None)
        self._run_background("Preparar datos para análisis", fn, self._on_prepare_done)

    def _run_train(self) -> None:
        fn = lambda: self._workflow.train(self.adv_dataset.text().strip(), self.adv_model.text().strip() or None)
        self._run_background("Crear modelo de predicción", fn, self._on_train_done)

    def _run_score(self) -> None:
        fn = lambda: self._workflow.score(
            self.adv_dataset.text().strip(), self.adv_model.text().strip(), self.score_limit.value()
        )
        self._run_background("Analizar citas y estimar riesgo", fn, self._on_score_done)

    def _run_drift(self) -> None:
        from_version = self.adv_prev_dataset.text().strip() or self.adv_dataset.text().strip()
        fn = lambda: self._workflow.drift(from_version, self.adv_dataset.text().strip())
        self._run_background("Detectar cambios en comportamiento", fn, self._on_drift_done)

    def _run_playbook_action(self) -> None:
        if self._accion_playbook_actual is None:
            return
        accion = self._accion_playbook_actual
        if accion.requiere_confirmacion:
            confirmar = QMessageBox.question(
                self,
                self._t("demo_ml.playbook.ejecucion.confirmacion.titulo"),
                self._t("demo_ml.playbook.ejecucion.confirmacion.mensaje"),
            )
            if confirmar != QMessageBox.StandardButton.Yes:
                return
        contexto = ContextoEjecucionPlaybook(
            from_date=self._from(),
            to_date=self._to(),
            score_limit=self.score_limit.value(),
            export_dir=self.export_dir.text().strip() or "./exports",
        )
        fn = lambda: self._playbook_ejecucion.ejecutar_accion(accion, contexto)
        self._run_background(self._t(accion.cta_key), fn, self._on_playbook_action_done)

    def _run_full_workflow(self) -> None:
        if self._is_running():
            return
        config = AnalyticsWorkflowConfig(
            export_dir=self.export_dir.text().strip() or "./exports",
            score_limit=self.score_limit.value(),
            drift_enabled=True,
            seed_if_missing=self.chk_seed_full.isChecked(),
        )
        self._run_id = uuid.uuid4().hex[:8]
        self._cancel_token = CancelToken()
        LOGGER.info("analytics_action_started", extra={"action": "Demo completa", "run_id": self._run_id})
        self._open_progress_dialog(self._STEPS)

        self._thread = QThread(self)
        self._workflow_worker = _WorkflowWorker(
            run_id=self._run_id,
            workflow=self._workflow,
            from_date=self._from(),
            to_date=self._to(),
            config=config,
            previous_dataset_version=self.adv_prev_dataset.text().strip() or None,
            seed_request=self._seed_request(),
            cancel_token=self._cancel_token,
        )
        self._workflow_worker.moveToThread(self._thread)
        self._thread.started.connect(self._workflow_worker.run)
        self._workflow_worker.progress.connect(self._on_workflow_progress)
        self._workflow_worker.finished.connect(self._on_workflow_done)
        self._workflow_worker.finished.connect(self._thread.quit)
        self._workflow_worker.finished.connect(self._workflow_worker.deleteLater)
        self._workflow_worker.error.connect(self._on_task_error)
        self._workflow_worker.error.connect(self._thread.quit)
        self._workflow_worker.error.connect(self._workflow_worker.deleteLater)
        self._thread.finished.connect(self._on_workflow_thread_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _run_background(
        self,
        action_name: str,
        fn: Callable[[], Any],
        on_done: Callable[[Any], None],
        close_dialog: bool = True,
        on_started: Callable[[], None] | None = None,
    ) -> None:
        if self._is_running():
            return
        self._run_id = uuid.uuid4().hex[:8]
        self._cancel_token = CancelToken()
        LOGGER.info("analytics_action_started", extra={"action": action_name, "run_id": self._run_id})
        if on_started is not None:
            on_started()
        self._thread = QThread(self)
        worker = _TaskWorker(self._run_id, fn)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.finished.connect(on_done)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(self._on_task_error)
        worker.failed.connect(self._thread.quit)
        worker.failed.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        if close_dialog:
            self._thread.finished.connect(self._close_progress_dialog)
        self._thread.start()

    def _open_progress_dialog(self, steps: list[str]) -> None:
        self.progress_dialog = ProgressDialog(self)
        self.progress_dialog.start(self._run_id, steps)
        self.progress_dialog.bind_cancel(self._on_cancel_requested)

    def _close_progress_dialog(self) -> None:
        dialog = getattr(self, "progress_dialog", None)
        if dialog is not None:
            dialog.close()

    def _on_cancel_requested(self) -> None:
        if self._cancel_token is not None:
            self._cancel_token.cancel()
        dialog = getattr(self, "progress_dialog", None)
        if dialog is not None:
            dialog.mark_cancel_requested()

    def _on_workflow_progress(self, percent: int, message: str) -> None:
        dialog = getattr(self, "progress_dialog", None)
        if dialog is None:
            return
        dialog.set_progress(percent)
        step_index = min(3, max(0, percent // 25))
        dialog.update(step_index, "done" if percent >= 100 else "running", message)
        LOGGER.info("analytics_progress", extra={"run_id": self._run_id, "progress": percent, "message": message})

    def _on_workflow_thread_finished(self) -> None:
        self._workflow_worker = None
        self._thread = None

    def _on_prepare_done(self, version: str) -> None:
        self.adv_dataset.setText(version)
        self._log(f"Preparación completada: {version}")
        self.card_citas.set_data("Listo", "Features disponibles", "ok")
        self._refresh_guided_state()

    def _on_train_done(self, payload: tuple[Any, str]) -> None:
        train_response, model_version = payload
        self._last_train = train_response
        self.adv_model.setText(model_version)
        subtitle = f"Recall test {train_response.test_metrics.recall:.2f} · Precision test {train_response.test_metrics.precision:.2f}"
        self.card_threshold.set_data(f"{train_response.calibrated_threshold:.2f}", subtitle, "ok")
        self._log("Modelo de predicción listo")
        texto = interpretar_entrenamiento(
            train_response.test_metrics.accuracy,
            train_response.test_metrics.precision,
            train_response.test_metrics.recall,
        )
        self._log(f"{texto.titulo}: {texto.significado}")
        self._log(f"Siguiente paso: {texto.recomendacion}")
        self._render_lectura_operativa(
            construir_lectura_operativa_metricas(
                train_response.test_metrics.accuracy,
                train_response.test_metrics.precision,
                train_response.test_metrics.recall,
                train_response.test_row_count,
            )
        )
        self._refresh_guided_state()

    def _on_score_done(self, response: Any) -> None:
        self._last_score = response
        self._update_score_cards(response)
        self._lista_trabajo_ml = self._construir_lista_trabajo_ml(response)
        self._render_lista_trabajo_ml()
        self._log(f"Análisis de riesgo completado: {response.total} citas")
        riesgo_alto = sum(1 for item in response.items if item.label == "risk")
        texto = interpretar_scoring(response.total, riesgo_alto)
        self._log(f"{texto.titulo}: {texto.significado}")
        self._log(f"Qué hacer ahora: {texto.recomendacion}")
        self._render_lectura_operativa(construir_lectura_operativa_scoring(response.total, riesgo_alto))
        self._refresh_guided_state()

    def _on_drift_done(self, response: Any) -> None:
        self._last_drift = response
        self._update_drift_card(response)
        self._log(f"Detección de cambios completada: {response.overall_flag}")
        texto = interpretar_drift(response)
        self._log(f"{texto.titulo}: {texto.significado}")
        self._log(f"Acción recomendada: {texto.recomendacion}")
        self._render_lectura_operativa(construir_lectura_operativa_drift(response))
        self._refresh_guided_state()

    def _on_playbook_action_done(self, resultado: ResultadoPasoPlaybook) -> None:
        self._ultimo_resultado_playbook = resultado
        detalle = resultado.detalle_humano or self._t(resultado.resumen_key)
        self._log(f"Playbook {resultado.accion_clave}: {detalle}")
        self._refresh_guided_state()

    def _on_workflow_done(self, result: AnalyticsWorkflowResult) -> None:
        self._last_result = result
        self.adv_dataset.setText(result.internal_versions["dataset_version"])
        self.adv_model.setText(result.internal_versions["model_version"])
        self.adv_summary.setPlainText(result.summary_text)
        self._persist_last_run(result)
        self._refresh_last_label()
        self._refresh_tables()
        self._refresh_export_files(result.export_paths)
        dialog = getattr(self, "progress_dialog", None)
        if dialog is not None:
            dialog.finish(True, result.summary_text)
            for index, step in enumerate(self._STEPS):
                dialog.update(index, "done", step)
        self._log(result.summary_text)
        self._render_lectura_operativa(construir_lectura_operativa_exportacion(len(result.export_paths)))
        self._refresh_guided_state()

    def _on_task_error(self, message: str) -> None:
        LOGGER.error("analytics_action_failed", extra={"run_id": self._run_id, "message": message})
        dialog = getattr(self, "progress_dialog", None)
        if dialog is not None:
            dialog.finish(False, message)
        self._log(f"Error: {message}")
        QMessageBox.warning(self, "Error en Analítica", message)

    def _seed_request(self) -> SeedDemoDataRequest:
        return SeedDemoDataRequest(
            seed=self.seed_seed.value(),
            n_doctors=self.seed_doctors.value(),
            n_patients=self.seed_patients.value(),
            n_appointments=self.seed_appointments.value(),
            from_date=self._from(),
            to_date=self._to(),
            incidence_rate=float(self.seed_incidence.text() or "0.15"),
        )

    def _from(self) -> str:
        return self.seed_from.date().toString("yyyy-MM-dd")

    def _to(self) -> str:
        return self.seed_to.date().toString("yyyy-MM-dd")

    def _refresh_tables(self) -> None:
        self._fill_table(self.tbl_doctors, [asdict(item) for item in self._facade.list_doctors(None, 200)])
        self._fill_table(self.tbl_patients, [asdict(item) for item in self._facade.list_patients(None, 200)])
        citas = self._facade.list_appointments(None, None, None, 200)
        self._fill_table(self.tbl_appointments, [asdict(item) for item in citas])
        self._fill_table(self.tbl_incidences, [asdict(item) for item in self._facade.list_incidences(None, 200)])
        self.card_citas.set_data(str(len(citas)), "Citas visibles en demo", "ok")

    def _fill_table(self, table: QTableWidget, rows: list[dict[str, Any]]) -> None:
        table.setRowCount(0)
        for row in rows:
            idx = table.rowCount()
            table.insertRow(idx)
            for col, value in enumerate(row.values()):
                table.setItem(idx, col, QTableWidgetItem(str(value)))

    def _construir_lista_trabajo_ml(self, score_response: Any) -> ListaTrabajoML:
        citas = self._facade.list_appointments(limit=500)
        return self._priorizacion_service.construir_lista_trabajo(score_response, citas)

    def _render_lista_trabajo_ml(self) -> None:
        if self._lista_trabajo_ml is None:
            self.lbl_priorizacion_resumen.setText(self._t("demo_ml.priorizacion.panel.vacio"))
            self.tbl_priorizacion_ml.setRowCount(0)
            return
        resumen = self._lista_trabajo_ml.resumen
        self.lbl_priorizacion_resumen.setText(
            self._t("demo_ml.priorizacion.panel.resumen_valor").format(
                total=resumen.total_items,
                alta=resumen.prioridad_alta,
                media=resumen.prioridad_media,
                baja=resumen.prioridad_baja,
                accion_fuerte=resumen.accion_fuerte_habilitada,
            )
        )
        filtro = self.cmb_priorizacion_filtro.currentData()
        filas = []
        for item in self._lista_trabajo_ml.items:
            if filtro != "todos" and item.prioridad.value != filtro:
                continue
            paciente = item.paciente or self._t("demo_ml.priorizacion.valor_no_disponible")
            filas.append(
                {
                    "cita": f"{item.cita_id} · {paciente}",
                    "prioridad": self._t(f"demo_ml.priorizacion.nivel.{item.prioridad.value}"),
                    "accion": self._t(item.accion_sugerida.descripcion_i18n_key),
                    "motivo": self._t(item.motivo.resumen_i18n_key),
                    "cautela": self._t(item.cautela_i18n_key),
                }
            )
        self._fill_table(self.tbl_priorizacion_ml, filas)

    def _persist_last_run(self, result: AnalyticsWorkflowResult) -> None:
        self._settings.setValue("last_run_ts", datetime.now().isoformat(timespec="seconds"))
        self._settings.setValue("last_export_dir", self.export_dir.text().strip() or "./exports")
        self._settings.setValue("last_summary_text", result.summary_text)
        self._settings.setValue("last_internal_versions", result.internal_versions)

    def _restore_settings(self) -> None:
        self.export_dir.setText(self._settings.value("last_export_dir", "./exports", str) or "./exports")
        versions = self._settings.value("last_internal_versions", {}) or {}
        if isinstance(versions, dict):
            self.adv_dataset.setText(str(versions.get("dataset_version", "")))
            self.adv_model.setText(str(versions.get("model_version", "")))
        self.adv_summary.setPlainText(self._settings.value("last_summary_text", "", str) or "")
        self._refresh_last_label()

    def _refresh_last_label(self) -> None:
        ts = self._settings.value("last_run_ts", "", str) or "sin fecha"
        summary = self._settings.value("last_summary_text", "Sin ejecuciones", str) or "Sin ejecuciones"
        self.lbl_last.setText(f"Último análisis: {ts} (ver detalles) · {summary}")

    def _refresh_export_files(self, exports: dict[str, str]) -> None:
        if not exports:
            self.lbl_export_files.setText(self._t("demo_ml.estado.export_sin_resultados"))
            return
        file_list = " · ".join(sorted(Path(path).name for path in exports.values()))
        self.lbl_export_files.setText(f"Archivos exportados: {file_list}")


    def _refresh_guided_state(self) -> None:
        estado = self._centro_service.construir_estado(self.export_dir.text().strip() or "./exports")
        self.btn_train.setEnabled(self._paso_habilitado(estado, "train"))
        self.btn_score.setEnabled(self._paso_habilitado(estado, "score"))
        self.btn_drift.setEnabled(self._paso_habilitado(estado, "drift"))
        self.btn_open_export.setEnabled(bool(estado.archivos_exportados))
        self.lbl_estado.setText(self._render_estado(estado))
        self.lbl_recomendado.setText(self._render_siguiente_paso(estado.siguiente_accion))
        self._render_recomendaciones(estado.recomendaciones)
        self._render_resumen_ejecutivo(estado.resumen_ejecutivo)
        self._render_playbooks(estado)
        self._refresh_export_files({name: name for name in estado.archivos_exportados}) if estado.archivos_exportados else None

    def _render_recomendaciones(self, recomendaciones) -> None:
        if not recomendaciones:
            texto_vacio = self._t("demo_ml.asistente.panel.vacio")
            self.lbl_reco_principal.setText(texto_vacio)
            self.lbl_reco_secundarias.setText(texto_vacio)
            self.lbl_reco_advertencias.setText(texto_vacio)
            return
        principal = recomendaciones[0]
        secundarios = [rec for rec in recomendaciones[1:] if rec.tipo != "bloqueo"]
        advertencias = [rec for rec in recomendaciones if rec.tipo in {"bloqueo", "advertencia"}]
        self.lbl_reco_principal.setText(self._texto_recomendacion(principal))
        self.lbl_reco_secundarias.setText("\n".join(self._texto_recomendacion(rec) for rec in secundarios[:3]))
        self.lbl_reco_advertencias.setText("\n".join(self._texto_recomendacion(rec) for rec in advertencias[:3]))

    def _texto_recomendacion(self, recomendacion) -> str:
        return (
            f"• {self._t(recomendacion.titulo_key)}\n"
            f"{self._t(recomendacion.explicacion_key)}\n"
            f"{self._t(recomendacion.motivo_key)}\n"
            f"{self._t(recomendacion.beneficio_key)}\n"
            f"{self._t(recomendacion.accion_key)} · {self._t(recomendacion.cta_key)}"
        )

    def _render_resumen_ejecutivo(self, resumen) -> None:
        self.lbl_resumen_estado.setText(self._t(resumen.estado_actual_key))
        self.lbl_resumen_falta.setText(self._t(resumen.que_falta_key))
        self.lbl_resumen_paso.setText(self._t(resumen.siguiente_paso_key))
        self.lbl_resumen_riesgo.setText(self._t(resumen.riesgo_principal_key))
        self.lbl_resumen_utilidad.setText(self._t(resumen.utilidad_inmediata_key))

    def _paso_habilitado(self, estado, clave: str) -> bool:
        for paso in estado.pasos:
            if paso.clave == clave:
                return paso.habilitado
        return False

    def _render_estado(self, estado) -> str:
        bloqueados = [paso for paso in estado.pasos if not paso.habilitado and paso.motivo_bloqueo]
        if not bloqueados:
            return self._t("demo_ml.estado.pipeline_listo")
        return self._t("demo_ml.estado.pipeline_bloqueado").format(motivo=bloqueados[0].motivo_bloqueo)

    def _render_siguiente_paso(self, siguiente: str) -> str:
        mapa = {
            "prepare": self._t("demo_ml.estado.siguiente.prepare"),
            "train": self._t("demo_ml.estado.siguiente.train"),
            "score": self._t("demo_ml.estado.siguiente.score"),
            "drift": self._t("demo_ml.estado.siguiente.drift"),
            "export": self._t("demo_ml.estado.siguiente.export"),
            "summary": self._t("demo_ml.estado.siguiente.summary"),
        }
        return mapa.get(siguiente, self._t("demo_ml.estado.siguiente.summary"))


    def _on_playbook_changed(self, _: int) -> None:
        self._playbook_seleccionado = self.cmb_playbook.currentData() or ""
        self._refresh_guided_state()

    def _render_playbooks(self, estado) -> None:
        playbooks = {item.codigo: item for item in estado.playbooks}
        if not playbooks:
            texto = self._t("demo_ml.playbook.panel.vacio")
            self.lbl_playbook_resumen.setText(texto)
            self.lbl_playbook_pasos.setText(texto)
            self.lbl_playbook_siguiente.setText(texto)
            self.lbl_playbook_progreso.setText(texto)
            self.lbl_playbook_resultado.setText(texto)
            self.btn_playbook_cta.setEnabled(False)
            return
        if self.cmb_playbook.count() != len(playbooks):
            self.cmb_playbook.blockSignals(True)
            self.cmb_playbook.clear()
            for codigo, playbook in playbooks.items():
                self.cmb_playbook.addItem(self._t(playbook.titulo_key), codigo)
            self.cmb_playbook.blockSignals(False)
        seleccionado = self._playbook_seleccionado or estado.playbook_sugerido
        index = self.cmb_playbook.findData(seleccionado)
        if index >= 0 and self.cmb_playbook.currentIndex() != index:
            self.cmb_playbook.blockSignals(True)
            self.cmb_playbook.setCurrentIndex(index)
            self.cmb_playbook.blockSignals(False)
        self._playbook_seleccionado = self.cmb_playbook.currentData() or estado.playbook_sugerido
        playbook = playbooks.get(self._playbook_seleccionado)
        if playbook is None:
            return
        prerequisitos = "\n".join(f"• {self._t(key)}" for key in playbook.prerequisitos_keys)
        resumen = (
            f"{self._t(playbook.descripcion_key)}\n"
            f"{self._t(playbook.para_que_key)}\n"
            f"{self._t(playbook.cuando_usar_key)}\n"
            f"{self._t('demo_ml.playbook.panel.prerequisitos')}:\n{prerequisitos}\n"
            f"{self._t(playbook.criterio_finalizacion_key)}\n"
            f"{self._t('demo_ml.playbook.panel.estado')}: {self._estado_playbook_text(playbook.estado_general)}"
        )
        self.lbl_playbook_resumen.setText(resumen)
        self.lbl_playbook_siguiente.setText(self._render_siguiente_paso(playbook.siguiente_paso_clave))
        estado_ejecucion = self._playbook_ejecucion.construir_estado(playbook)
        progreso = estado_ejecucion.progreso
        self.lbl_playbook_progreso.setText(
            self._t("demo_ml.playbook.panel.progreso_texto").format(
                completados=progreso.completados,
                total=progreso.total_pasos,
                bloqueados=progreso.bloqueados,
            )
        )
        self._accion_playbook_actual = estado_ejecucion.accion_siguiente
        self.btn_playbook_cta.setText(self._t(self._accion_playbook_actual.cta_key))
        self.btn_playbook_cta.setEnabled(self._accion_playbook_actual.permiso != "bloqueada")
        if self._ultimo_resultado_playbook is None:
            self.lbl_playbook_resultado.setText(self._t("demo_ml.playbook.panel.vacio"))
        else:
            self.lbl_playbook_resultado.setText(
                self._t("demo_ml.playbook.panel.resultado_texto").format(
                    estado=self._estado_playbook_text(self._ultimo_resultado_playbook.estado),
                    detalle=self._ultimo_resultado_playbook.detalle_humano or self._t(self._ultimo_resultado_playbook.resumen_key),
                    siguiente=self._render_siguiente_paso(self._ultimo_resultado_playbook.siguiente_paso_clave),
                )
            )
        texto_pasos = "\n\n".join(self._render_paso_playbook(paso) for paso in playbook.pasos)
        self.lbl_playbook_pasos.setText(texto_pasos)

    def _render_paso_playbook(self, paso) -> str:
        return (
            f"• {self._t(paso.nombre_key)} [{self._estado_playbook_text(paso.estado)}]\n"
            f"{self._t(paso.que_hace_key)}\n"
            f"{self._t(paso.por_que_importa_key)}\n"
            f"{self._t(paso.necesitas_key)}\n"
            f"{self._t(paso.resultado_key)}\n"
            f"{self._t(paso.mirar_despues_key)}\n"
            f"{self._t('demo_ml.playbook.panel.cta')}: {self._t(paso.cta_key)}\n"
            f"{self._t(paso.motivo_estado_key)}"
        )

    def _estado_playbook_text(self, estado: str) -> str:
        return self._t(f"demo_ml.playbook.estado.{estado}")

    def _is_running(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "Analítica", "Ya hay una operación en curso")
            return True
        return False

    def _log(self, msg: str) -> None:
        self.txt_logs.append(msg)

    def _reset_kpi_cards(self) -> None:
        self.card_citas.set_data("—", "Pendiente", "neutral")
        self.card_risk.set_data("—", "Pendiente", "neutral")
        self.card_threshold.set_data("—", "Disponible tras crear modelo", "neutral")
        self.card_drift.set_data("—", "Ejecute detección de cambios", "neutral")
        self._reset_lectura_operativa_panel()

    def _reset_lectura_operativa_panel(self) -> None:
        texto = self._t("demo_ml.operativa.panel.vacio")
        self.lbl_operativa_semaforo.setText(texto)
        self.lbl_operativa_significado.setText(texto)
        self.lbl_operativa_utilidad.setText(texto)
        self.lbl_operativa_accion.setText(texto)
        self.lbl_operativa_no_concluir.setText(texto)

    def _render_lectura_operativa(self, lectura: LecturaOperativaML) -> None:
        semaforo = self._t(f"demo_ml.operativa.semaforo.{lectura.semaforo.value}")
        self.lbl_operativa_semaforo.setText(
            self._t("demo_ml.operativa.panel.semaforo_valor").format(
                semaforo=semaforo,
                confianza=lectura.nivel_confianza,
            )
        )
        self.lbl_operativa_significado.setText(self._t(lectura.resumen_humano.clave).format(**lectura.resumen_humano.params))
        self.lbl_operativa_utilidad.setText(self._t(lectura.utilidad.descripcion.clave))
        self.lbl_operativa_accion.setText(self._t(lectura.accion_sugerida.descripcion.clave))
        self.lbl_operativa_no_concluir.setText(self._t(lectura.cuando_no_concluir_fuerte.clave))

    def _update_score_cards(self, response: Any) -> None:
        labels = Counter(item.label for item in response.items)
        high_count = labels.get("risk", 0)
        total = max(response.total, 1)
        risk_pct = (high_count / total) * 100
        subtitle = f"Riesgo alto: {high_count} / {response.total}"
        self.card_citas.set_data(str(response.total), "Total de citas analizadas", "ok")
        state = "bad" if risk_pct >= 30 else "warn" if risk_pct >= 15 else "ok"
        self.card_risk.set_data(f"{risk_pct:.1f}%", subtitle, state)

    def _update_drift_card(self, report: Any) -> None:
        severity, message, psi_max = explain_drift(report)
        state = {"GREEN": "ok", "AMBER": "warn", "RED": "bad"}[severity.value]
        self.card_drift.set_data(severity.value, f"PSI máx: {psi_max:.3f} · {message}", state)

    def _open_export_folder(self) -> None:
        folder = Path(self.export_dir.text().strip() or "./exports").resolve()
        if not folder.exists():
            QMessageBox.information(self, "Exportación", "La carpeta de exportación todavía no existe.")
            return
        try:
            self._open_folder_in_os(folder)
            self._log(f"Carpeta abierta: {folder.as_posix()}")
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("open_export_folder_failed", extra={"path": folder.as_posix(), "error": str(exc)})
            QMessageBox.information(self, "Exportación", "No fue posible abrir la carpeta automáticamente.")

    def _open_folder_in_os(self, folder: Path) -> None:
        if os.name == "nt":
            os.startfile(str(folder))  # type: ignore[attr-defined]
            return
        command = "open" if shutil.which("open") else "xdg-open"
        if shutil.which(command) is None:
            raise RuntimeError("No hay comando de apertura disponible")
        subprocess.Popen([command, folder.as_posix()])
