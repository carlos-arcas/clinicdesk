from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable

from PySide6.QtCore import QDate, QObject, QSettings, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
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

from clinicdesk.app.application.services.analytics_workflow_service import (
    AnalyticsWorkflowConfig,
    AnalyticsWorkflowResult,
    AnalyticsWorkflowService,
)
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.demo_run_service import CancelToken
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest
from clinicdesk.app.bootstrap_logging import get_logger, set_run_context
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


class PageDemoML(QWidget):
    _STEPS = ["Preparar análisis", "Entrenar", "Calcular riesgo", "Detectar cambios"]

    def __init__(self, facade: DemoMLFacade, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._facade = facade
        self._workflow = AnalyticsWorkflowService(facade)
        self._settings = QSettings("clinicdesk", "analytics_demo")
        self._thread: QThread | None = None
        self._cancel_token: CancelToken | None = None
        self._run_id = ""
        self._last_result: AnalyticsWorkflowResult | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.addWidget(self._build_left_column())
        splitter.addWidget(self._build_right_column())
        splitter.setSizes([650, 550])
        root.addWidget(splitter)
        self._restore_settings()
        self._refresh_tables()

    def _build_left_column(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(self._build_seed_panel())
        layout.addWidget(self._build_tables())
        return panel

    def _build_right_column(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(self._build_workflow_panel())
        layout.addWidget(self._build_advanced_panel())
        layout.addWidget(QLabel("Resumen de actividad"))
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        layout.addWidget(self.txt_logs)
        return panel

    def _build_seed_panel(self) -> QWidget:
        box = QGroupBox("Datos demo")
        form = QFormLayout(box)
        self.seed_seed = QSpinBox(); self.seed_seed.setRange(1, 999999); self.seed_seed.setValue(123)
        self.seed_doctors = QSpinBox(); self.seed_doctors.setRange(1, 300); self.seed_doctors.setValue(10)
        self.seed_patients = QSpinBox(); self.seed_patients.setRange(1, 2000); self.seed_patients.setValue(80)
        self.seed_appointments = QSpinBox(); self.seed_appointments.setRange(1, 10000); self.seed_appointments.setValue(300)
        self.seed_from = QDateEdit(); self.seed_from.setCalendarPopup(True); self.seed_from.setDate(QDate.currentDate().addDays(-30))
        self.seed_to = QDateEdit(); self.seed_to.setCalendarPopup(True); self.seed_to.setDate(QDate.currentDate())
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
        self.score_limit = QSpinBox(); self.score_limit.setRange(1, 10000); self.score_limit.setValue(20)
        self.export_dir = QLineEdit(self._settings.value("last_export_dir", "./exports", str) or "./exports")
        self.lbl_last = QLabel("Último análisis: sin ejecuciones")
        self.btn_full = QPushButton("Ejecutar Demo Completa")
        self.btn_full.clicked.connect(self._run_full_workflow)
        cards = QHBoxLayout()
        self.btn_prepare = QPushButton("1) Preparar análisis")
        self.btn_train = QPushButton("2) Entrenar")
        self.btn_score = QPushButton("3) Calcular riesgo")
        self.btn_drift = QPushButton("4) Detectar cambios")
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
        form.addRow(self.lbl_last)
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
        self._run_background("Preparar análisis", lambda: self._workflow.prepare_analysis(self._from(), self._to(), self.adv_dataset.text().strip() or None), self._on_prepare_done)

    def _run_train(self) -> None:
        self._run_background("Entrenar", lambda: self._workflow.train(self.adv_dataset.text().strip(), self.adv_model.text().strip() or None), self._on_train_done)

    def _run_score(self) -> None:
        fn = lambda: self._workflow.score(self.adv_dataset.text().strip(), self.adv_model.text().strip(), self.score_limit.value())
        self._run_background("Calcular riesgo", fn, self._on_score_done)

    def _run_drift(self) -> None:
        from_version = self.adv_prev_dataset.text().strip() or self.adv_dataset.text().strip()
        self._run_background("Detectar cambios", lambda: self._workflow.drift(from_version, self.adv_dataset.text().strip()), self._on_drift_done)

    def _run_full_workflow(self) -> None:
        config = AnalyticsWorkflowConfig(
            export_dir=self.export_dir.text().strip() or "./exports",
            score_limit=self.score_limit.value(),
            drift_enabled=True,
            seed_if_missing=self.chk_seed_full.isChecked(),
        )
        seed_request = self._seed_request()

        def _execute() -> AnalyticsWorkflowResult:
            return self._workflow.run_full_workflow(
                self._from(),
                self._to(),
                config,
                previous_dataset_version=self.adv_prev_dataset.text().strip() or None,
                seed_request=seed_request,
                cancel_token=self._cancel_token,
                progress_cb=self._on_workflow_progress,
            )

        self._run_background(
            "Demo completa",
            _execute,
            self._on_workflow_done,
            close_dialog=False,
            on_started=lambda: self._open_progress_dialog(self._STEPS),
        )

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

    def _on_workflow_progress(self, percent: int, status: str, message: str) -> None:
        dialog = getattr(self, "progress_dialog", None)
        if dialog is None:
            return
        dialog.set_progress(percent)
        step_index = min(3, max(0, percent // 25))
        dialog.update(step_index, "running" if status == "running" else "done", message)
        LOGGER.info("analytics_progress", extra={"run_id": self._run_id, "progress": percent, "message": message})

    def _on_prepare_done(self, version: str) -> None:
        self.adv_dataset.setText(version)
        self._log(f"Preparar análisis completado: {version}")

    def _on_train_done(self, payload: tuple[Any, str]) -> None:
        train_response, model_version = payload
        self._last_train = train_response
        self.adv_model.setText(model_version)
        self._log("Entrenamiento completado")

    def _on_score_done(self, response: Any) -> None:
        self._last_score = response
        self._log(f"Cálculo de riesgo completado: {response.total} casos")

    def _on_drift_done(self, response: Any) -> None:
        self._last_drift = response
        self._log(f"Detección de cambios completada: {response.overall_flag}")

    def _on_workflow_done(self, result: AnalyticsWorkflowResult) -> None:
        self._last_result = result
        self.adv_dataset.setText(result.internal_versions["dataset_version"])
        self.adv_model.setText(result.internal_versions["model_version"])
        self.adv_summary.setPlainText(result.summary_text)
        self._persist_last_run(result)
        self._refresh_last_label()
        self._refresh_tables()
        dialog = getattr(self, "progress_dialog", None)
        if dialog is not None:
            dialog.finish(True, result.summary_text)
            dialog.update(0, "done", "Preparar análisis")
            dialog.update(1, "done", "Entrenar")
            dialog.update(2, "done", "Calcular riesgo")
            dialog.update(3, "done", "Detectar cambios")
        self._log(result.summary_text)

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
        self._fill_table(self.tbl_appointments, [asdict(item) for item in self._facade.list_appointments(None, None, None, 200)])
        self._fill_table(self.tbl_incidences, [asdict(item) for item in self._facade.list_incidences(None, 200)])

    def _fill_table(self, table: QTableWidget, rows: list[dict[str, Any]]) -> None:
        table.setRowCount(0)
        for row in rows:
            idx = table.rowCount()
            table.insertRow(idx)
            for col, value in enumerate(row.values()):
                table.setItem(idx, col, QTableWidgetItem(str(value)))

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

    def _is_running(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "Analítica", "Ya hay una operación en curso")
            return True
        return False

    def _log(self, msg: str) -> None:
        self.txt_logs.append(msg)
