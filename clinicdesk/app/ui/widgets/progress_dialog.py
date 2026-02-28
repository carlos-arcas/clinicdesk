from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.ui.log_buffer_handler import LogBufferHandler

_STATUS_ICON = {"pending": "⏳", "running": "⏳", "done": "✅", "error": "❌"}


class ProgressDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, max_log_lines: int = 8) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ejecución en progreso")
        self.setModal(True)
        self._run_id = ""
        self._max_log_lines = max_log_lines
        self._steps: list[str] = []
        self._cancelled = False
        self._timer = QTimer(self)
        self._timer.setInterval(350)
        self._timer.timeout.connect(self._refresh_log)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.lbl_title = QLabel("Preparando ejecución…")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.lst_steps = QListWidget()
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.btn_cancel = QPushButton("Cancelar")
        row = QHBoxLayout()
        row.addWidget(self.btn_cancel)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.progress)
        layout.addWidget(self.lst_steps)
        layout.addWidget(QLabel("Log reciente"))
        layout.addWidget(self.txt_log)
        layout.addLayout(row)

    def start(self, run_id: str, steps: list[str]) -> None:
        self._run_id = run_id
        self._steps = steps
        self._cancelled = False
        self.progress.setValue(0)
        self.lbl_title.setText("Iniciando…")
        self.lst_steps.clear()
        self.txt_log.clear()
        for name in steps:
            self.lst_steps.addItem(self._label("pending", name, "Pendiente"))
        self._timer.start()
        self.show()

    def update(self, step_index: int, status: str, message: str) -> None:
        if 0 <= step_index < self.lst_steps.count():
            step_name = self._steps[step_index]
            self.lst_steps.item(step_index).setText(self._label(status, step_name, message))
            self.lst_steps.scrollToItem(self.lst_steps.item(step_index))
        self.lbl_title.setText(message)

    def set_progress(self, value: int) -> None:
        self.progress.setValue(max(0, min(value, 100)))

    def finish(self, ok: bool, summary: str) -> None:
        self._timer.stop()
        status = "Finalizado" if ok else "Finalizado con incidencias"
        self.lbl_title.setText(f"{status}: {summary}")
        self.progress.setValue(100 if ok else self.progress.value())

    def bind_cancel(self, callback) -> None:
        self.btn_cancel.clicked.connect(callback)

    def mark_cancel_requested(self) -> None:
        self._cancelled = True
        self.btn_cancel.setEnabled(False)
        self.lbl_title.setText("Cancelando…")

    def _refresh_log(self) -> None:
        lines = LogBufferHandler.shared_snapshot(self._run_id)
        tail = lines[-self._max_log_lines :]
        self.txt_log.setPlainText("\n".join(tail))

    def _label(self, status: str, step: str, message: str) -> str:
        return f"{_STATUS_ICON.get(status, '⏳')} {step}: {message}"
