from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO


@dataclass(frozen=True, slots=True)
class AccionLoteDTO:
    tipo: str
    cita_ids: tuple[int, ...]
    canal: str | None = None


class WorkerRecordatoriosLote(QObject):
    started = Signal(str)
    ok = Signal(object)
    fail = Signal(str)
    finished = Signal()

    def __init__(self, facade, accion: AccionLoteDTO) -> None:
        super().__init__()
        self._facade = facade
        self._accion = accion

    def run(self) -> None:
        try:
            self.started.emit(self._accion.tipo)
            self.ok.emit(self._resolver_accion())
        except Exception:
            self.fail.emit("confirmaciones.lote.error_accionable")
        finally:
            self.finished.emit()

    def _resolver_accion(self) -> ResultadoLoteRecordatoriosDTO:
        if self._accion.tipo == "PREPARAR":
            return self._facade.preparar_lote_uc.ejecutar(self._accion.cita_ids, self._accion.canal or "WHATSAPP")
        return self._facade.marcar_enviado_lote_uc.ejecutar(self._accion.cita_ids, self._accion.canal)
