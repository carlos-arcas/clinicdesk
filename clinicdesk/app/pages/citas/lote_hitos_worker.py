from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from clinicdesk.app.application.citas import (
    HitoAtencion,
    ModoTimestampHito,
    RegistrarHitoAtencionCita,
    RegistrarHitosLoteError,
    RegistrarHitosAtencionEnLote,
)
from clinicdesk.app.infrastructure.sqlite.db import get_connection
from clinicdesk.app.infrastructure.sqlite.repos_citas_hitos import CitasHitosRepository


@dataclass(frozen=True, slots=True)
class AccionLoteHitosDTO:
    cita_ids: tuple[int, ...]
    hito: HitoAtencion
    modo_timestamp: ModoTimestampHito


class _RelojSistema:
    def ahora(self) -> datetime:
        return datetime.now().replace(microsecond=0)


class WorkerHitosLote(QObject):
    started = Signal()
    finished_ok = Signal(object)
    finished_error = Signal(str)
    finished = Signal()

    def __init__(self, db_path: str, accion: AccionLoteHitosDTO) -> None:
        super().__init__()
        self._db_path = db_path
        self._accion = accion

    def run(self) -> None:
        try:
            self.started.emit()
            con = get_connection(self._db_path)
            repo = CitasHitosRepository(con)
            registrar = RegistrarHitoAtencionCita(repo, _RelojSistema())
            uc = RegistrarHitosAtencionEnLote(registrar_hito_uc=registrar, repositorio=repo)
            self.finished_ok.emit(uc.ejecutar(self._accion.cita_ids, self._accion.hito, self._accion.modo_timestamp))
        except RegistrarHitosLoteError as exc:
            self.finished_error.emit(exc.reason_code)
        except Exception:
            self.finished_error.emit("citas.hitos.lote.error_guardar")
        finally:
            try:
                con.close()  # type: ignore[name-defined]
            except Exception:
                pass
            self.finished.emit()
