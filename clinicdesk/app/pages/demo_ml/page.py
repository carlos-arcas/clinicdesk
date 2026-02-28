from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from PySide6.QtCore import QDate, QObject, QThread, Signal
from PySide6.QtWidgets import (
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

from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade


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


class PageDemoML(QWidget):
    def __init__(self, facade: DemoMLFacade, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._facade = facade
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
        layout.addWidget(QLabel("Logs"))
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        layout.addWidget(self.txt_logs)
        layout.addWidget(QLabel("Resultados (score/drift)"))
        self.tbl_results = QTableWidget(0, 4)
        self.tbl_results.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tbl_results)
        return panel

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
        rows = [{"cita": item.cita_id, "score": f"{item.score:.3f}", "label": item.label, "reasons": ", ".join(item.reasons)} for item in response.items]
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
        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "Demo & ML", "Hay una operación en curso")
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
