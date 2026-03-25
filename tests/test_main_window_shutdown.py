from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QCoreApplication

    from clinicdesk.app.i18n import I18nManager
    from clinicdesk.app.ui.jobs.job_manager import JobCancelledError
    from clinicdesk.app.ui.main_window import MainWindow
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)


pytestmark = [pytest.mark.ui, pytest.mark.uiqt, pytest.mark.integration]


def test_main_window_cierre_controlado_con_job_activo(qtbot, container) -> None:
    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None, shutdown_timeout_ms=1_000)
    qtbot.addWidget(window)
    window.show()

    def worker_factory():
        def _worker(cancel_token, report_progress):
            report_progress(20, "job.seed_demo.progress.preflight")
            while not cancel_token.is_cancelled:
                QCoreApplication.processEvents()
            raise JobCancelledError()

        return _worker

    window.run_premium_job(
        job_id="job-close",
        title_key="job.rotate_crypto.title",
        worker_factory=worker_factory,
        cancellable=True,
        toast_success_key="job.done",
        toast_failed_key="job.failed",
        toast_cancelled_key="job.cancelled",
    )

    qtbot.waitUntil(lambda: window._job_manager.tiene_jobs_activos())
    window.close()

    assert window._cierre_controlado_en_progreso is True
    assert window.isVisible() is True

    qtbot.waitUntil(lambda: not window._job_manager.tiene_jobs_activos())
    qtbot.waitUntil(lambda: not window.isVisible())


def test_main_window_timeout_no_cierra_app_y_permite_reintento(qtbot, container) -> None:
    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None, shutdown_timeout_ms=30)
    qtbot.addWidget(window)
    window.show()
    liberar_worker = {"ok": False}

    def worker_factory():
        def _worker(_cancel_token, report_progress):
            report_progress(30, "job.seed_demo.progress.preflight")
            while not liberar_worker["ok"]:
                QCoreApplication.processEvents()
            return {"ok": True}

        return _worker

    window.run_premium_job(
        job_id="job-bloqueado",
        title_key="job.rotate_crypto.title",
        worker_factory=worker_factory,
        cancellable=True,
        toast_success_key="job.done",
        toast_failed_key="job.failed",
        toast_cancelled_key="job.cancelled",
    )

    qtbot.waitUntil(lambda: window._job_manager.tiene_jobs_activos())
    window.close()
    primer_timer = window._shutdown_timeout_timer
    assert primer_timer is not None

    window.close()
    assert window._shutdown_timeout_timer is primer_timer

    qtbot.waitUntil(lambda: window._shutdown_timeout_timer is None)
    assert window.isVisible() is True
    assert window._cierre_controlado_en_progreso is False
    assert window._permitir_cierre_directo is False

    window.close()
    assert window._cierre_controlado_en_progreso is True
    assert window._shutdown_timeout_timer is not None
    liberar_worker["ok"] = True
    qtbot.waitUntil(lambda: not window._job_manager.tiene_jobs_activos())


def test_main_window_run_premium_job_invoca_callback_on_failed(qtbot, container) -> None:
    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None)
    qtbot.addWidget(window)
    window.show()
    errores: list[str] = []

    def worker_factory():
        def _worker(_cancel_token, report_progress):
            report_progress(15, "job.seed_demo.progress.preflight")
            raise RuntimeError("fallo_controlado")

        return _worker

    window.run_premium_job(
        job_id="job-fail-callback",
        title_key="job.rotate_crypto.title",
        worker_factory=worker_factory,
        cancellable=True,
        toast_success_key="job.done",
        toast_failed_key="job.failed",
        toast_cancelled_key="job.cancelled",
        on_failed=errores.append,
    )

    qtbot.waitUntil(lambda: errores == ["fallo_controlado"])
