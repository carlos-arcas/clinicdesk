from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QThread

from clinicdesk.app.pages.pacientes.coordinadores.contexto_operativo import CoordinadorContextoPacientes
from clinicdesk.app.pages.pacientes.workers_pacientes import RelayBusquedaRapidaPacientes
from clinicdesk.app.ui.workers.listado_async_workers import CargaPacientesWorker

LOGGER = logging.getLogger(__name__)


class CoordinadorBusquedaRapidaPacientes:
    def __init__(self, *, contexto: CoordinadorContextoPacientes) -> None:
        self._contexto = contexto
        self._thread: QThread | None = None
        self._worker: CargaPacientesWorker | None = None
        self._relay: RelayBusquedaRapidaPacientes | None = None
        self._on_done: Callable[[list[Any]], None] | None = None

    def preparar(self, on_done: Callable[[list[Any]], None]) -> int | None:
        if self._thread is not None and self._thread.isRunning():
            return None
        self._on_done = on_done
        return self._contexto.nueva_busqueda_rapida()

    def registrar_thread(
        self,
        *,
        thread: QThread | None,
        worker: CargaPacientesWorker | None,
        relay: RelayBusquedaRapidaPacientes | None,
    ) -> None:
        self._thread = thread
        self._worker = worker
        self._relay = relay

    def finalizar_thread(self) -> None:
        self._thread = None
        self._worker = None
        self._relay = None

    def consumir_resultado(self, payload: object, token: int) -> bool:
        if not self._contexto.puede_consumir_busqueda_rapida(token):
            return False
        if not callable(self._on_done):
            return False
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        self._on_done(rows)
        return True

    def registrar_error(self, error_type: str, token: int) -> bool:
        if token != self._contexto.token_busqueda_rapida:
            return False
        LOGGER.warning(
            "pacientes_busqueda_rapida_error",
            extra={"action": "pacientes_busqueda_rapida_error", "error": error_type, "token": token},
        )
        return True
