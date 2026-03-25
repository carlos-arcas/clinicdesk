from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Callable

from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class DecisionCierre:
    permitir_cierre: bool = False
    ignorar_evento: bool = True
    iniciar_shutdown: bool = False
    completar_cierre: bool = False
    restaurar_estado_ui: bool = False
    toast_key: str | None = None


class ControladorCierreApp:
    def __init__(
        self,
        *,
        timeout_ms: int = 5_000,
        reloj_ms: Callable[[], int] | None = None,
    ) -> None:
        self._timeout_ms = max(timeout_ms, 0)
        self._reloj_ms = reloj_ms or (lambda: int(monotonic() * 1000))
        self._cierre_en_progreso = False
        self._permitir_cierre_directo = False
        self._deadline_ms: int | None = None
        self._inicio_ms: int | None = None
        self._shutdown_seq = 0
        self._shutdown_id: str | None = None
        self._jobs_iniciales: tuple[str, ...] = ()

    @property
    def cierre_en_progreso(self) -> bool:
        return self._cierre_en_progreso

    @property
    def permitir_cierre_directo(self) -> bool:
        return self._permitir_cierre_directo

    def solicitar_cierre(self, *, ids_jobs_activos: tuple[str, ...]) -> DecisionCierre:
        ahora = self._reloj_ms()
        if self._permitir_cierre_directo:
            return DecisionCierre(permitir_cierre=True, ignorar_evento=False)
        if self._cierre_en_progreso:
            return DecisionCierre()
        if not ids_jobs_activos:
            self._permitir_cierre_directo = True
            return DecisionCierre(permitir_cierre=True, ignorar_evento=False)

        self._cierre_en_progreso = True
        self._inicio_ms = ahora
        self._deadline_ms = ahora + self._timeout_ms
        self._jobs_iniciales = ids_jobs_activos
        self._shutdown_seq += 1
        self._shutdown_id = f"shutdown-{self._shutdown_seq}"
        LOGGER.info(
            "shutdown_intento_iniciado",
            extra={
                "reason_code": "shutdown_started",
                "shutdown_id": self._shutdown_id,
                "timeout_ms": self._timeout_ms,
                "total_jobs": len(ids_jobs_activos),
                "job_ids": ids_jobs_activos,
            },
        )
        return DecisionCierre(iniciar_shutdown=True, toast_key="job.shutdown.requested")

    def registrar_cierre_completado(self) -> DecisionCierre:
        if not self._cierre_en_progreso:
            return DecisionCierre()
        ahora = self._reloj_ms()
        duracion_ms = None if self._inicio_ms is None else max(ahora - self._inicio_ms, 0)
        LOGGER.info(
            "shutdown_completado",
            extra={
                "reason_code": "shutdown_completed",
                "shutdown_id": self._shutdown_id,
                "duration_ms": duracion_ms,
                "total_jobs": len(self._jobs_iniciales),
            },
        )
        self._cierre_en_progreso = False
        self._permitir_cierre_directo = True
        self._deadline_ms = None
        self._inicio_ms = None
        self._jobs_iniciales = ()
        return DecisionCierre(completar_cierre=True)

    def intentar_timeout(self, *, ids_jobs_activos: tuple[str, ...]) -> DecisionCierre:
        if not self._cierre_en_progreso or self._deadline_ms is None:
            return DecisionCierre()
        ahora = self._reloj_ms()
        if ahora < self._deadline_ms:
            return DecisionCierre()

        duracion_ms = None if self._inicio_ms is None else max(ahora - self._inicio_ms, 0)
        LOGGER.warning(
            "shutdown_abortado",
            extra={
                "reason_code": "shutdown_timeout",
                "shutdown_id": self._shutdown_id,
                "timeout_ms": self._timeout_ms,
                "duration_ms": duracion_ms,
                "total_jobs": len(self._jobs_iniciales),
                "jobs_bloqueando_total": len(ids_jobs_activos),
                "jobs_bloqueando_ids": ids_jobs_activos,
            },
        )
        self._cierre_en_progreso = False
        self._permitir_cierre_directo = False
        self._deadline_ms = None
        self._inicio_ms = None
        self._jobs_iniciales = ()
        return DecisionCierre(restaurar_estado_ui=True, toast_key="job.shutdown.timeout")
