from __future__ import annotations

from dataclasses import dataclass, replace
from threading import Event
from typing import Any, Callable, Literal

from PySide6.QtCore import QObject, QThread, Signal

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
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(
            lambda progress, message_key, _job_id=job_id: self._on_progress(_job_id, progress, message_key)
        )
        worker.finished.connect(lambda result, _job_id=job_id: self._on_finished(_job_id, result))
        worker.failed.connect(lambda error, _job_id=job_id: self._on_failed(_job_id, error))
        worker.cancelled.connect(lambda _job_id=job_id: self._on_cancelled(_job_id))
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.cancelled.connect(worker.deleteLater)
        thread.finished.connect(lambda _job_id=job_id: self._cleanup(_job_id))
        self._threads[job_id] = thread
        self._workers[job_id] = worker
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

    def _on_progress(self, job_id: str, progress: int, message_key: str) -> None:
        state = self._states[job_id]
        actualizado = replace(state, progress=progress, message_key=message_key)
        self._states[job_id] = actualizado
        self.progress.emit(actualizado)

    def _on_finished(self, job_id: str, result: Any) -> None:
        state = self._states[job_id]
        actualizado = replace(state, progress=100, status="finished")
        self._states[job_id] = actualizado
        self.finished.emit(actualizado, result)

    def _on_failed(self, job_id: str, error: str) -> None:
        state = self._states[job_id]
        actualizado = replace(state, status="failed")
        self._states[job_id] = actualizado
        self.failed.emit(actualizado, error)

    def _on_cancelled(self, job_id: str) -> None:
        state = self._states[job_id]
        actualizado = replace(state, status="cancelled")
        self._states[job_id] = actualizado
        self.cancelled.emit(actualizado)

    def _cleanup(self, job_id: str) -> None:
        self._threads.pop(job_id, None)
        self._workers.pop(job_id, None)
        self._tokens.pop(job_id, None)
