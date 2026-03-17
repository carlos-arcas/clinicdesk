from __future__ import annotations

from dataclasses import dataclass, replace
from threading import Event
from typing import Any, Callable, Literal

from PySide6.QtCore import QObject, QThread, Signal, Slot

from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)

JobStatus = Literal["pending", "running", "finished", "failed", "cancelled"]
ProgressCallback = Callable[[int, str], None]
JobCallable = Callable[["CancelToken", ProgressCallback], Any]
WorkerFactory = Callable[[], JobCallable]


@dataclass(frozen=True, slots=True)
class JobState:
    id: str
    title_key: str
    progress: int
    message_key: str
    cancellable: bool
    status: JobStatus


class CancelToken:
    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()


class JobCancelledError(RuntimeError):
    pass


class _JobWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, job_callable: JobCallable, cancel_token: CancelToken) -> None:
        super().__init__()
        self._job_callable = job_callable
        self._cancel_token = cancel_token

    def run(self) -> None:
        try:
            result = self._job_callable(self._cancel_token, self._emit_progress)
            if self._cancel_token.is_cancelled:
                self.cancelled.emit()
                return
            self.finished.emit(result)
        except JobCancelledError:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))

    def _emit_progress(self, progress: int, message_key: str) -> None:
        self.progress.emit(max(0, min(progress, 100)), message_key)


class _JobRelay(QObject):
    progress = Signal(str, int, str)
    finished = Signal(str, object)
    failed = Signal(str, str)
    cancelled = Signal(str)
    thread_finished = Signal(str)

    def __init__(self, job_id: str) -> None:
        super().__init__()
        self._job_id = job_id

    @Slot(int, str)
    def on_worker_progress(self, progress: int, message_key: str) -> None:
        self.progress.emit(self._job_id, progress, message_key)

    @Slot(object)
    def on_worker_finished(self, result: Any) -> None:
        self.finished.emit(self._job_id, result)

    @Slot(str)
    def on_worker_failed(self, error: str) -> None:
        self.failed.emit(self._job_id, error)

    @Slot()
    def on_worker_cancelled(self) -> None:
        self.cancelled.emit(self._job_id)

    @Slot()
    def on_thread_finished(self) -> None:
        self.thread_finished.emit(self._job_id)


class JobManager(QObject):
    started = Signal(object)
    progress = Signal(object)
    finished = Signal(object, object)
    failed = Signal(object, str)
    cancelled = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._threads: dict[str, QThread] = {}
        self._workers: dict[str, _JobWorker] = {}
        self._relays: dict[str, _JobRelay] = {}
        self._states: dict[str, JobState] = {}
        self._tokens: dict[str, CancelToken] = {}

    def run_job(self, job_id: str, title_key: str, worker_factory: WorkerFactory, cancellable: bool = True) -> JobState:
        if job_id in self._threads:
            return self._states[job_id]
        cancel_token = CancelToken()
        state = JobState(
            id=job_id,
            title_key=title_key,
            progress=0,
            message_key="job.progress.starting",
            cancellable=cancellable,
            status="running",
        )
        worker = _JobWorker(worker_factory(), cancel_token)
        relay = _JobRelay(job_id)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(relay.on_worker_progress)
        worker.finished.connect(relay.on_worker_finished)
        worker.failed.connect(relay.on_worker_failed)
        worker.cancelled.connect(relay.on_worker_cancelled)
        relay.progress.connect(self._on_progress)
        relay.finished.connect(self._on_finished)
        relay.failed.connect(self._on_failed)
        relay.cancelled.connect(self._on_cancelled)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.cancelled.connect(worker.deleteLater)
        thread.finished.connect(relay.on_thread_finished)
        relay.thread_finished.connect(self._cleanup)
        self._threads[job_id] = thread
        self._workers[job_id] = worker
        self._relays[job_id] = relay
        self._states[job_id] = state
        self._tokens[job_id] = cancel_token
        self.started.emit(state)
        thread.start()
        return state

    def cancel_job(self, job_id: str) -> bool:
        token = self._tokens.get(job_id)
        if token is None:
            return False
        token.cancel()
        return True

    def get_state(self, job_id: str) -> JobState | None:
        return self._states.get(job_id)

    @Slot(str, int, str)
    def _on_progress(self, job_id: str, progress: int, message_key: str) -> None:
        state = self._states.get(job_id)
        if state is None:
            LOGGER.info("job_progress_omitido", extra={"job_id": job_id, "razon": "job_no_vigente"})
            return
        actualizado = replace(state, progress=progress, message_key=message_key)
        self._states[job_id] = actualizado
        self.progress.emit(actualizado)

    @Slot(str, object)
    def _on_finished(self, job_id: str, result: Any) -> None:
        state = self._states.get(job_id)
        if state is None:
            LOGGER.info("job_finished_omitido", extra={"job_id": job_id, "razon": "job_no_vigente"})
            return
        if state.status == "cancelled":
            LOGGER.info("job_finished_omitido", extra={"job_id": job_id, "razon": "job_cancelado"})
            return
        actualizado = replace(state, progress=100, status="finished")
        self._states[job_id] = actualizado
        self.finished.emit(actualizado, result)

    @Slot(str, str)
    def _on_failed(self, job_id: str, error: str) -> None:
        state = self._states.get(job_id)
        if state is None:
            LOGGER.info("job_failed_omitido", extra={"job_id": job_id, "razon": "job_no_vigente"})
            return
        if state.status == "cancelled":
            LOGGER.info("job_failed_omitido", extra={"job_id": job_id, "razon": "job_cancelado"})
            return
        actualizado = replace(state, status="failed")
        self._states[job_id] = actualizado
        self.failed.emit(actualizado, error)

    @Slot(str)
    def _on_cancelled(self, job_id: str) -> None:
        state = self._states.get(job_id)
        if state is None:
            LOGGER.info("job_cancelled_omitido", extra={"job_id": job_id, "razon": "job_no_vigente"})
            return
        actualizado = replace(state, status="cancelled")
        self._states[job_id] = actualizado
        self.cancelled.emit(actualizado)

    @Slot(str)
    def _cleanup(self, job_id: str) -> None:
        LOGGER.info("job_cleanup", extra={"job_id": job_id})
        self._threads.pop(job_id, None)
        self._workers.pop(job_id, None)
        self._relays.pop(job_id, None)
        self._tokens.pop(job_id, None)
