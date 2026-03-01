from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal

from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo

from clinicdesk.app.application.prediccion_ausencias import EntrenamientoPrediccionError


@dataclass(frozen=True, slots=True)
class EntrenamientoFailPayload:
    reason_code: str
    error_type: str
    error_message: str


def construir_payload_error_entrenamiento(exc: Exception) -> EntrenamientoFailPayload:
    if isinstance(exc, EntrenamientoPrediccionError):
        reason_code = exc.reason_code
    else:
        reason_code = "unexpected_error"
    return EntrenamientoFailPayload(
        reason_code=reason_code,
        error_type=type(exc).__name__,
        error_message=str(exc),
    )


class EntrenarPrediccionWorker(QObject):
    started = Signal()
    ok = Signal(object)
    fail = Signal(object)
    finished = Signal()

    # Compatibilidad con conexiones existentes.
    success = ok
    error = fail

    def __init__(self, entrenar_uc, proveedor_conexion: ProveedorConexionSqlitePorHilo | None = None) -> None:
        super().__init__()
        self._entrenar_uc = entrenar_uc
        self._proveedor_conexion = proveedor_conexion

    def run(self) -> None:
        self.started.emit()
        try:
            resultado = self._entrenar_uc.ejecutar()
            self.ok.emit(resultado)
        except Exception as exc:  # noqa: BLE001
            self.fail.emit(construir_payload_error_entrenamiento(exc))
        finally:
            self._cerrar_conexion_hilo_actual()
            self.finished.emit()

    def _cerrar_conexion_hilo_actual(self) -> None:
        if self._proveedor_conexion is None:
            return
        self._proveedor_conexion.cerrar_conexion_del_hilo_actual()


class RunnerEntrenamientoPrediccion(QObject):
    started = Signal()
    ok = Signal(object)
    fail = Signal(object)
    finished = Signal()

    success = ok
    error = fail

    def __init__(self, entrenar_uc, proveedor_conexion: ProveedorConexionSqlitePorHilo | None = None) -> None:
        super().__init__()
        self._thread = QThread()
        self._worker = EntrenarPrediccionWorker(entrenar_uc, proveedor_conexion)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.started.connect(self.started)
        self._worker.ok.connect(self.ok)
        self._worker.fail.connect(self.fail)
        self._worker.finished.connect(self.finished)
        self._worker.ok.connect(self._thread.quit)
        self._worker.fail.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

    def start(self) -> None:
        self._thread.start()
