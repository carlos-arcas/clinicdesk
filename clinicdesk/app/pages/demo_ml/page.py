from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from PySide6.QtCore import QDate, QObject, QSettings, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
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

from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.demo_run_service import (
    CancelToken,
    DemoRunConfig,
    DemoRunResult,
    DemoRunService,
)


class _TaskWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            self.finished.emit(self._fn())
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class _DemoRunWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(int, str)

    def __init__(self, service: DemoRunService, cfg: DemoRunConfig, token: CancelToken) -> None:
        super().__init__()
        self._service = service
        self._cfg = cfg
        self._token = token

    def run(self) -> None:
        try:
            result = self._service.run_full_demo(self._cfg, progress_cb=self.progress.emit, cancel_token=self._token)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class PageDemoML(QWidget):
    def __init__(self, facade: DemoMLFacade, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._facade = facade
        self._demo_runner = DemoRunService(facade)
        self._settings = QSettings("clinicdesk", "demo_ml")
        self._cancel_token: CancelToken | None = None
        self._last_train = None
        self._last_score = None
        self._last_drift = None
        self._thread: QThread | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.addWidget(self._build_left_column())
        splitter.addWidget(self._build_right_column())
        splitter.setSizes([700, 500])
        root.addWidget(splitter)
        self._restore_settings()
        self._refresh_tables()

    def _build_left_column(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(self._build_seed_panel())
        layout.addWidget(self._build_search_panel())
        layout.addWidget(self._build_tables())
        return panel

    def _build_right_column(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(self._build_ml_panel())
        layout.addWidget(self._build_full_demo_panel())
        layout.addWidget(QLabel("Logs"))
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        layout.addWidget(self.txt_logs)
        layout.addWidget(QLabel("Resultados (score/drift)"))
        self.tbl_results = QTableWidget(0, 4)
        self.tbl_results.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tbl_results)
        return panel

    def _build_full_demo_panel(self) -> QWidget:
        box = QGroupBox("One-click Demo")
        form = QFormLayout(box)
        self.btn_run_full = QPushButton("Run Full Demo")
        self.btn_cancel_full = QPushButton("Cancel")
        self.btn_cancel_full.setEnabled(False)
        self.btn_copy_cli = QPushButton("Copy CLI commands")
        self.btn_copy_cli.setEnabled(False)
        self.progress_full = QProgressBar()
        self.progress_full.setRange(0, 100)
        self.progress_full.setValue(0)
        self.lbl_summary = QLabel("Sin ejecución")
        self.lst_cli = QListWidget()
        self.lst_exports = QListWidget()
        row = QHBoxLayout()
        row.addWidget(self.btn_run_full)
        row.addWidget(self.btn_cancel_full)
        row.addWidget(self.btn_copy_cli)
        self.btn_run_full.clicked.connect(self._run_full_demo)
        self.btn_cancel_full.clicked.connect(self._cancel_full_demo)
        self.btn_copy_cli.clicked.connect(self._copy_cli_commands)
        form.addRow(row)
        form.addRow("Progreso", self.progress_full)
        form.addRow("Resumen", self.lbl_summary)
        form.addRow("Exports", self.lst_exports)
        form.addRow("CLI", self.lst_cli)
        return box

    def _build_seed_panel(self) -> QWidget:
        box = QGroupBox("Seed Demo")
        form = QFormLayout(box)
        self.seed_seed = QSpinBox(); self.seed_seed.setRange(1, 999999); self.seed_seed.setValue(123)
        self.seed_doctors = QSpinBox(); self.seed_doctors.setRange(1, 300); self.seed_doctors.setValue(10)
        self.seed_patients = QSpinBox(); self.seed_patients.setRange(1, 2000); self.seed_patients.setValue(80)
        self.seed_appointments = QSpinBox(); self.seed_appointments.setRange(1, 10000); self.seed_appointments.setValue(300)
        self.seed_from = QDateEdit(); self.seed_from.setCalendarPopup(True); self.seed_from.setDate(QDate.currentDate().addDays(-30))
        self.seed_to = QDateEdit(); self.seed_to.setCalendarPopup(True); self.seed_to.setDate(QDate.currentDate())
        self.seed_incidence = QLineEdit("0.15")
        btn_seed = QPushButton("Ejecutar SeedDemoData")
        btn_seed.clicked.connect(self._run_seed)
        form.addRow("Seed", self.seed_seed)
        form.addRow("Médicos", self.seed_doctors)
        form.addRow("Pacientes", self.seed_patients)
        form.addRow("Citas", self.seed_appointments)
        form.addRow("Desde", self.seed_from)
        form.addRow("Hasta", self.seed_to)
        form.addRow("Incidence rate", self.seed_incidence)
        form.addRow(btn_seed)
        return box

    def _build_search_panel(self) -> QWidget:
        box = QGroupBox("Búsqueda")
        row = QHBoxLayout(box)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("buscar por texto")
        self.btn_refresh = QPushButton("Refrescar tablas")
        self.btn_refresh.clicked.connect(self._refresh_tables)
        row.addWidget(self.txt_search)
        row.addWidget(self.btn_refresh)
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

    def _build_ml_panel(self) -> QWidget:
        box = QGroupBox("ML actions")
        form = QFormLayout(box)
        self.ml_from = QDateEdit(); self.ml_from.setCalendarPopup(True); self.ml_from.setDate(self.seed_from.date())
        self.ml_to = QDateEdit(); self.ml_to.setCalendarPopup(True); self.ml_to.setDate(self.seed_to.date())
        self.ml_dataset = QLineEdit()
        self.ml_model = QLineEdit("m_demo_ui")
        self.ml_predictor = QLineEdit("baseline")
        self.ml_limit = QSpinBox(); self.ml_limit.setRange(1, 10000); self.ml_limit.setValue(20)
        self.ml_from_version = QLineEdit(); self.ml_to_version = QLineEdit()
        self.ml_export_dir = QLineEdit("./exports")
        row_buttons = QHBoxLayout()
        for text, handler in [
            ("build-features", self._run_build_features),
            ("train", self._run_train),
            ("score", self._run_score),
            ("drift", self._run_drift),
            ("export", self._run_export),
        ]:
            button = QPushButton(text)
            button.clicked.connect(handler)
            row_buttons.addWidget(button)
        form.addRow("From", self.ml_from)
        form.addRow("To", self.ml_to)
        form.addRow("Dataset version", self.ml_dataset)
        form.addRow("Model version", self.ml_model)
        form.addRow("Predictor", self.ml_predictor)
        form.addRow("Score limit", self.ml_limit)
        form.addRow("Drift from version", self.ml_from_version)
        form.addRow("Drift to version", self.ml_to_version)
        form.addRow("Export dir", self.ml_export_dir)
        form.addRow(row_buttons)
        return box

    def _run_full_demo(self) -> None:
        if self._is_running():
            return
        self.progress_full.setValue(0)
        self.lst_cli.clear()
        self.lst_exports.clear()
        self.btn_copy_cli.setEnabled(False)
        cfg = self._build_full_demo_config()
        self._cancel_token = CancelToken()
        self._set_full_demo_running(True)
        self._thread = QThread(self)
        worker = _DemoRunWorker(self._demo_runner, cfg, self._cancel_token)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.progress.connect(self._on_full_demo_progress)
        worker.finished.connect(self._on_full_demo_done)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(self._on_task_error)
        worker.failed.connect(self._thread.quit)
        worker.failed.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(lambda: self._set_full_demo_running(False))
        self._thread.start()

    def _build_full_demo_config(self) -> DemoRunConfig:
        return DemoRunConfig(
            seed=self.seed_seed.value(),
            n_doctors=self.seed_doctors.value(),
            n_patients=self.seed_patients.value(),
            n_appointments=self.seed_appointments.value(),
            from_date=self.seed_from.date().toString("yyyy-MM-dd"),
            to_date=self.seed_to.date().toString("yyyy-MM-dd"),
            incidence_rate=float(self.seed_incidence.text() or "0.15"),
            export_dir=self.ml_export_dir.text().strip() or "./exports",
            feature_store_path="./data/feature_store",
            model_store_path="./data/model_store",
            score_limit=self.ml_limit.value(),
            prev_dataset_version=self._settings.value("prev_dataset_version", "", str) or None,
        )

    def _cancel_full_demo(self) -> None:
        if self._cancel_token is not None:
            self._cancel_token.cancel()
            self._log("Cancel solicitado para Run Full Demo")

    def _on_full_demo_progress(self, pct: int, message: str) -> None:
        self.progress_full.setValue(pct)
        self._log(message)

    def _on_full_demo_done(self, result: DemoRunResult) -> None:
        if not result.ok:
            self.lbl_summary.setText("Run Full Demo cancelado o incompleto")
            return
        self.ml_dataset.setText(result.dataset_version)
        self.ml_model.setText(result.model_version)
        self.ml_from_version.setText(self._settings.value("prev_dataset_version", "", str) or result.dataset_version)
        self.ml_to_version.setText(result.dataset_version)
        self._persist_result_settings(result)
        self._render_full_demo_result(result)
        self._refresh_tables()

    def _persist_result_settings(self, result: DemoRunResult) -> None:
        prev_dataset = self._settings.value("last_dataset_version", "", str) or ""
        if prev_dataset:
            self._settings.setValue("prev_dataset_version", prev_dataset)
        self._settings.setValue("last_dataset_version", result.dataset_version)
        self._settings.setValue("last_model_version", result.model_version)
        self._settings.setValue("last_export_dir", self.ml_export_dir.text().strip() or "./exports")

    def _render_full_demo_result(self, result: DemoRunResult) -> None:
        self.lbl_summary.setText(
            f"dataset={result.dataset_version} | model={result.model_version} | exports={len(result.export_paths)}"
        )
        self.lst_exports.clear()
        for name, path in result.export_paths.items():
            self.lst_exports.addItem(f"{name}: {path}")
        self.lst_cli.clear()
        for command in result.cli_commands:
            self.lst_cli.addItem(command)
        self.btn_copy_cli.setEnabled(bool(result.cli_commands))
        self._log("Run Full Demo finalizado")

    def _copy_cli_commands(self) -> None:
        lines = [self.lst_cli.item(i).text() for i in range(self.lst_cli.count())]
        QApplication.clipboard().setText("\n".join(lines))
        self._log(f"CLI copiado ({len(lines)} comandos)")

    def _set_full_demo_running(self, running: bool) -> None:
        self.btn_run_full.setEnabled(not running)
        self.btn_cancel_full.setEnabled(running)

    def _restore_settings(self) -> None:
        self.ml_dataset.setText(self._settings.value("last_dataset_version", "", str) or "")
        self.ml_model.setText(self._settings.value("last_model_version", "m_demo_ui", str) or "m_demo_ui")
        self.ml_export_dir.setText(self._settings.value("last_export_dir", "./exports", str) or "./exports")
        self.ml_from_version.setText(self._settings.value("prev_dataset_version", "", str) or "")

    def _is_running(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "Demo & ML", "Hay una operación en curso")
            return True
        return False

    def _mk_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _run_seed(self) -> None:
        from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest

        request = SeedDemoDataRequest(
            seed=self.seed_seed.value(),
            n_doctors=self.seed_doctors.value(),
            n_patients=self.seed_patients.value(),
            n_appointments=self.seed_appointments.value(),
            from_date=self.seed_from.date().toString("yyyy-MM-dd"),
            to_date=self.seed_to.date().toString("yyyy-MM-dd"),
            incidence_rate=float(self.seed_incidence.text() or "0.15"),
        )
        self._run_async(lambda: self._facade.seed_demo(request), self._on_seed_done)

    def _on_seed_done(self, response: Any) -> None:
        self.ml_dataset.setText(response.dataset_version)
        self._log(f"seed ok: dataset={response.dataset_version} citas={response.appointments}")
        self._refresh_tables()

    def _refresh_tables(self) -> None:
        query = self.txt_search.text().strip() or None
        self._fill_table(self.tbl_doctors, [asdict(item) for item in self._facade.list_doctors(query, 200)])
        self._fill_table(self.tbl_patients, [asdict(item) for item in self._facade.list_patients(query, 200)])
        self._fill_table(
            self.tbl_appointments,
            [asdict(item) for item in self._facade.list_appointments(query, None, None, 200)],
        )
        self._fill_table(self.tbl_incidences, [asdict(item) for item in self._facade.list_incidences(query, 200)])

    def _run_build_features(self) -> None:
        self._run_async(
            lambda: self._facade.build_features(
                self.ml_from.date().toString("yyyy-MM-dd"),
                self.ml_to.date().toString("yyyy-MM-dd"),
                self.ml_dataset.text().strip() or None,
            ),
            self._on_build_done,
        )

    def _on_build_done(self, version: str) -> None:
        self.ml_dataset.setText(version)
        self._log(f"build-features ok: version={version}")

    def _run_train(self) -> None:
        self._run_async(
            lambda: self._facade.train(self.ml_dataset.text().strip(), self.ml_model.text().strip() or None),
            self._on_train_done,
        )

    def _on_train_done(self, response: Any) -> None:
        self._last_train = response
        self.ml_model.setText(response.model_version)
        self._log(
            f"train ok: model={response.model_version} "
            f"test_acc={response.test_metrics.accuracy:.3f} threshold={response.calibrated_threshold:.2f}"
        )

    def _run_score(self) -> None:
        self._run_async(
            lambda: self._facade.score(
                self.ml_dataset.text().strip(),
                predictor_kind=self.ml_predictor.text().strip() or "baseline",
                model_version=self.ml_model.text().strip() or None,
                limit=self.ml_limit.value(),
            ),
            self._on_score_done,
        )

    def _on_score_done(self, response: Any) -> None:
        self._last_score = response
        self._log(f"score ok: version={response.version} total={response.total}")
        rows = [
            {
                "cita": item.cita_id,
                "score": f"{item.score:.3f}",
                "label": item.label,
                "reasons": ", ".join(item.reasons),
            }
            for item in response.items
        ]
        self._fill_generic_results(["cita", "score", "label", "reasons"], rows)

    def _run_drift(self) -> None:
        self._run_async(
            lambda: self._facade.drift(self.ml_from_version.text().strip(), self.ml_to_version.text().strip()),
            self._on_drift_done,
        )

    def _on_drift_done(self, response: Any) -> None:
        self._last_drift = response
        self._log(f"drift ok: from={response.from_version} to={response.to_version} overall={response.overall_flag}")
        rows = [
            {"feature": key, "psi": f"{value:.4f}", "from": response.from_version, "to": response.to_version}
            for key, value in sorted(response.psi_by_feature.items())
        ]
        self._fill_generic_results(["feature", "psi", "from", "to"], rows)

    def _run_export(self) -> None:
        out = self.ml_export_dir.text().strip() or "./exports"
        lines = []
        dataset = self.ml_dataset.text().strip()
        if dataset:
            lines.append(self._facade.export_features(dataset, out))
        if self._last_train is not None:
            lines.append(self._facade.export_metrics(self._last_train, out))
        if self._last_score is not None:
            model_version = self.ml_model.text().strip() or "baseline"
            threshold = self._last_train.calibrated_threshold if self._last_train else self._facade.default_baseline_threshold()
            lines.append(
                self._facade.export_scoring(
                    self._last_score,
                    predictor_kind=self.ml_predictor.text().strip() or "baseline",
                    model_version=model_version,
                    threshold_used=threshold,
                    output_path=out,
                )
            )
        if self._last_drift is not None:
            lines.append(self._facade.export_drift(self._last_drift, out))
        self._log("export ok:\n" + "\n".join(lines))

    def _fill_table(self, table: QTableWidget, rows: list[dict[str, Any]]) -> None:
        table.setRowCount(0)
        for row in rows:
            idx = table.rowCount()
            table.insertRow(idx)
            for col, value in enumerate(row.values()):
                table.setItem(idx, col, QTableWidgetItem(str(value)))

    def _fill_generic_results(self, headers: list[str], rows: list[dict[str, Any]]) -> None:
        self.tbl_results.setColumnCount(len(headers))
        self.tbl_results.setHorizontalHeaderLabels(headers)
        self._fill_table(self.tbl_results, rows)

    def _run_async(self, fn: Callable[[], Any], on_done: Callable[[Any], None]) -> None:
        if self._is_running():
            return
        self._thread = QThread(self)
        worker = _TaskWorker(fn)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.finished.connect(on_done)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(self._on_task_error)
        worker.failed.connect(self._thread.quit)
        worker.failed.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_task_error(self, message: str) -> None:
        self._log(f"error: {message}")
        QMessageBox.warning(self, "Error de operación", message)

    def _log(self, msg: str) -> None:
        self.txt_logs.append(msg)
