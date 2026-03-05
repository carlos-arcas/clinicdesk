from __future__ import annotations

from pathlib import Path

from clinicdesk.app.ui.jobs.job_manager import JobCancelledError


def crear_worker_exportacion(*, ejecutar_exportacion, filtros, preset_rango: str | None, ruta_guardado: str):
    def _worker(cancel_token, report_progress):
        report_progress(15, "job.export_auditoria.progress.preflight")
        if cancel_token.is_cancelled:
            raise JobCancelledError()
        report_progress(55, "job.export_auditoria.progress.export")
        exp = ejecutar_exportacion(filtros, preset_rango=preset_rango)
        if cancel_token.is_cancelled:
            raise JobCancelledError()
        report_progress(85, "job.export_auditoria.progress.write")
        Path(ruta_guardado).write_text(exp.csv_texto, encoding="utf-8")
        report_progress(100, "job.export_auditoria.progress.done")
        return ruta_guardado

    return _worker
