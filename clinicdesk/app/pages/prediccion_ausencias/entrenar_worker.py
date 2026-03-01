from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from clinicdesk.app.application.prediccion_ausencias import EntrenamientoPrediccionError


class EntrenarPrediccionWorker(QObject):
    started = Signal()
    ok = Signal(object)
    fail = Signal(str)
    finished = Signal()

    # Compatibilidad con conexiones existentes.
    success = ok
    error = fail

    def __init__(self, entrenar_uc) -> None:
        super().__init__()
        self._entrenar_uc = entrenar_uc

    def run(self) -> None:
        self.started.emit()
        try:
            resultado = self._entrenar_uc.ejecutar()
            self.ok.emit(resultado)
        except EntrenamientoPrediccionError as exc:
            self.fail.emit(exc.reason_code)
        except Exception:  # noqa: BLE001
            self.fail.emit("unexpected_error")
        finally:
            self.finished.emit()


class RunnerEntrenamientoPrediccion(QObject):
    started = Signal()
    ok = Signal(object)
    fail = Signal(str)
    finished = Signal()

    success = ok
    error = fail

    def __init__(self, entrenar_uc) -> None:
        super().__init__()
        self._thread = QThread()
        self._worker = EntrenarPrediccionWorker(entrenar_uc)
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
