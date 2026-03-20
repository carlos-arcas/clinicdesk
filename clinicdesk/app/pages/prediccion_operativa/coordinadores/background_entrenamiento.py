from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, QThread

from clinicdesk.app.pages.prediccion_operativa.coordinadores.runs_entrenamiento import RunEntrenamiento
from clinicdesk.app.pages.prediccion_operativa.workers import RelayEntrenamientoOperativo, WorkerEntrenarOperativo


@dataclass(slots=True)
class _RuntimeEntrenamiento:
    thread: QThread
    worker: WorkerEntrenarOperativo
    relay: RelayEntrenamientoOperativo


class CoordinadorBackgroundEntrenamientoPrediccionOperativa:
    def __init__(self, owner: QObject) -> None:
        self._owner = owner
        self._runtime_por_tipo: dict[str, _RuntimeEntrenamiento | None] = {"duracion": None, "espera": None}

    def iniciar_entrenamiento(
        self,
        run: RunEntrenamiento,
        ejecutar: Callable[[], object],
        cerrar_conexion: Callable[[], None] | None,
        on_ok: Callable[[str, int, object], None],
        on_fail: Callable[[str, int, object], None],
        on_thread_finished: Callable[[str, int], None],
    ) -> None:
        thread = QThread(self._owner)
        worker = WorkerEntrenarOperativo(ejecutar, cerrar_conexion)
        relay = RelayEntrenamientoOperativo(run.tipo, run.token)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.ok.connect(relay.on_worker_ok)
        worker.fail.connect(relay.on_worker_fail)
        relay.ok.connect(on_ok)
        relay.fail.connect(on_fail)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(relay.on_hilo_finalizado)
        relay.hilo_finalizado.connect(on_thread_finished)
        thread.finished.connect(thread.deleteLater)
        self._runtime_por_tipo[run.tipo] = _RuntimeEntrenamiento(thread=thread, worker=worker, relay=relay)
        thread.start()

    def limpiar(self, tipo: str) -> None:
        self._runtime_por_tipo[tipo] = None

    def tiene_hilos_activos(self) -> bool:
        return any(runtime is not None for runtime in self._runtime_por_tipo.values())
