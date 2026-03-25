from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from clinicdesk.app.ui.jobs.job_manager import JobCancelledError, JobManager


def _get_app() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def _wait_until(predicate, timeout_ms: int = 2000) -> None:
    loop = QEventLoop()

    def check() -> None:
        if predicate():
            loop.quit()

    timer = QTimer()
    timer.timeout.connect(check)
    timer.start(10)
    QTimer.singleShot(timeout_ms, loop.quit)
    check()
    loop.exec()
    timer.stop()


def test_job_manager_progress_and_finish() -> None:
    _get_app()
    manager = JobManager()
    eventos: list[tuple[str, int, str]] = []

    manager.progress.connect(lambda state: eventos.append((state.id, state.progress, state.message_key)))
    terminado: list[bool] = []
    manager.finished.connect(lambda _state, _result: terminado.append(True))

    def worker_factory():
        def _worker(_cancel_token, report_progress):
            report_progress(30, "job.export_auditoria.progress.preflight")
            report_progress(70, "job.export_auditoria.progress.export")
            return {"ok": True}

        return _worker

    manager.run_job("job-ok", "job.export_auditoria.title", worker_factory, cancellable=True)
    _wait_until(lambda: bool(terminado))

    assert terminado == [True]
    assert eventos[0][1] == 30
    assert eventos[-1][1] == 70
    _wait_until(lambda: not manager.tiene_jobs_activos())
    assert manager.ids_jobs_activos() == ()
    assert manager.resumen_recursos_activos() == {
        "threads": 0,
        "workers": 0,
        "relays": 0,
        "tokens": 0,
        "states": 0,
    }


def test_job_manager_cancel_emite_cancelled() -> None:
    _get_app()
    manager = JobManager()
    cancelado: list[bool] = []
    manager.cancelled.connect(lambda _state: cancelado.append(True))

    def worker_factory():
        def _worker(cancel_token, report_progress):
            report_progress(20, "job.seed_demo.progress.preflight")
            while not cancel_token.is_cancelled:
                QCoreApplication.processEvents()
            raise JobCancelledError()

        return _worker

    manager.run_job("job-cancel", "job.rotate_crypto.title", worker_factory, cancellable=True)
    manager.cancel_job("job-cancel")
    _wait_until(lambda: bool(cancelado))

    assert cancelado == [True]


def test_job_manager_failed_no_emite_finished() -> None:
    _get_app()
    manager = JobManager()
    errores: list[str] = []
    finalizados: list[bool] = []
    manager.failed.connect(lambda _state, error: errores.append(error))
    manager.finished.connect(lambda _state, _result: finalizados.append(True))

    def worker_factory():
        def _worker(_cancel_token, _report_progress):
            raise RuntimeError("boom")

        return _worker

    manager.run_job("job-fail", "job.export_auditoria.title", worker_factory, cancellable=True)
    _wait_until(lambda: bool(errores))

    assert errores == ["boom"]
    assert finalizados == []


def test_job_manager_solicitar_cierre_seguro_emite_cierre_completado() -> None:
    _get_app()
    manager = JobManager()
    cierre_completado: list[bool] = []
    cancelado: list[bool] = []
    manager.cierre_seguro_completado.connect(lambda: cierre_completado.append(True))
    manager.cancelled.connect(lambda _state: cancelado.append(True))

    def worker_factory():
        def _worker(cancel_token, report_progress):
            report_progress(10, "job.seed_demo.progress.preflight")
            while not cancel_token.is_cancelled:
                QCoreApplication.processEvents()
            raise JobCancelledError()

        return _worker

    manager.run_job("job-shutdown", "job.rotate_crypto.title", worker_factory, cancellable=True)
    ids = manager.solicitar_cierre_seguro()

    assert ids == ("job-shutdown",)
    _wait_until(lambda: bool(cierre_completado))
    assert cancelado == [True]
    assert cierre_completado == [True]
    assert manager.resumen_recursos_activos()["threads"] == 0


def test_job_manager_ignora_finalizacion_duplicada() -> None:
    _get_app()
    manager = JobManager()
    estados: list[str] = []
    manager.finished.connect(lambda state, _result: estados.append(state.status))

    def worker_factory():
        def _worker(_cancel_token, _report_progress):
            return {"ok": True}

        return _worker

    manager.run_job("job-dup", "job.export_auditoria.title", worker_factory, cancellable=True)
    _wait_until(lambda: bool(estados))
    manager._on_finished("job-dup", {"ok": True})

    assert estados == ["finished"]
