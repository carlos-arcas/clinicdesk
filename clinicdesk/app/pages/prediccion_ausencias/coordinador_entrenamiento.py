from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from clinicdesk.app.pages.prediccion_ausencias.entrenar_worker import construir_payload_error_entrenamiento
from clinicdesk.app.ui.jobs.job_manager import JobCancelledError


@runtime_checkable
class _PremiumJobRunner(Protocol):
    def run_premium_job(
        self,
        *,
        job_id: str,
        title_key: str,
        worker_factory,
        cancellable: bool,
        toast_success_key: str,
        toast_failed_key: str,
        toast_cancelled_key: str,
        on_success=None,
        on_failed=None,
    ) -> None: ...


def crear_worker_entrenamiento_prediccion(*, entrenar_uc, proveedor_conexion):
    def _worker(cancel_token, report_progress):
        report_progress(10, "job.prediccion_ausencias_entrenar.progress.preflight")
        if cancel_token.is_cancelled:
            raise JobCancelledError()
        report_progress(55, "job.prediccion_ausencias_entrenar.progress.entrenando")
        try:
            resultado = entrenar_uc.ejecutar()
        except Exception as exc:  # noqa: BLE001
            payload = construir_payload_error_entrenamiento(exc)
            raise RuntimeError(payload.reason_code) from exc
        finally:
            if proveedor_conexion is not None:
                proveedor_conexion.cerrar_conexion_del_hilo_actual()
        if cancel_token.is_cancelled:
            raise JobCancelledError()
        report_progress(85, "job.prediccion_ausencias_entrenar.progress.refrescando")
        report_progress(100, "job.prediccion_ausencias_entrenar.progress.done")
        return resultado

    return _worker


class CoordinadorEntrenamientoPrediccionAusencias:
    def __init__(self, *, entrenar_uc, proveedor_conexion) -> None:
        self._entrenar_uc = entrenar_uc
        self._proveedor_conexion = proveedor_conexion

    def iniciar(
        self,
        *,
        parent_window: object,
        on_success: Callable[[object], None],
        on_failed: Callable[[str], None],
    ) -> bool:
        if not isinstance(parent_window, _PremiumJobRunner):
            return False
        parent_window.run_premium_job(
            job_id="prediccion_ausencias_entrenar",
            title_key="job.prediccion_ausencias_entrenar.title",
            worker_factory=lambda: crear_worker_entrenamiento_prediccion(
                entrenar_uc=self._entrenar_uc,
                proveedor_conexion=self._proveedor_conexion,
            ),
            cancellable=True,
            toast_success_key="prediccion.entrenar.ok",
            toast_failed_key="prediccion.entrenar.error.no_preparar",
            toast_cancelled_key="job.cancelled",
            on_success=on_success,
            on_failed=on_failed,
        )
        return True
