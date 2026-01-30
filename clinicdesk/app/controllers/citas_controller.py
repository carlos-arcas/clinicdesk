from __future__ import annotations

from typing import List

from PySide6.QtWidgets import QMessageBox, QWidget

from clinicdesk.app.container import AppContainer
from clinicdesk.app.queries.citas_queries import CitaRow, CitasQueries
from clinicdesk.app.application.usecases.crear_cita import CrearCitaRequest, CrearCitaUseCase, PendingWarningsError

from clinicdesk.app.pages.citas.dialogs.dialog_cita_form import CitaFormDialog
from clinicdesk.app.pages.dialog_override import OverrideDialog
from clinicdesk.app.ui.error_presenter import present_error


class CitasController:
    """Controlador de la Page de Citas (UI)."""

    def __init__(self, parent: QWidget, container: AppContainer) -> None:
        self._parent = parent
        self._c = container
        self._q = CitasQueries(container)
        self._uc_crear = CrearCitaUseCase(container)

    def load_citas_for_date(self, yyyy_mm_dd: str) -> List[CitaRow]:
        return self._q.list_by_date(yyyy_mm_dd)

    def create_cita_flow(self, default_date: str) -> bool:
        dlg = CitaFormDialog(self._parent, default_date=default_date, container=self._c)
        if dlg.exec() != dlg.Accepted:
            return False

        data = dlg.get_data()
        if not data:
            return False

        req = CrearCitaRequest(
            paciente_id=data.paciente_id,
            medico_id=data.medico_id,
            sala_id=data.sala_id,
            inicio=data.inicio,
            fin=data.fin,
            motivo=data.motivo,
            observaciones=data.observaciones,
            estado="PROGRAMADA",
            override=False,
            nota_override=None,
            confirmado_por_personal_id=None,
        )

        try:
            self._uc_crear.execute(req)
            return True

        except PendingWarningsError as e:
            od = OverrideDialog(
                self._parent,
                title="Confirmar guardado con advertencias",
                warnings=e.warnings,
                container=self._c,
            )
            if od.exec() != od.Accepted:
                return False

            decision = od.get_decision()
            if not decision.accepted:
                return False

            req.override = True
            req.nota_override = decision.nota_override
            req.confirmado_por_personal_id = decision.confirmado_por_personal_id

            self._uc_crear.execute(req)
            return True

        except Exception as ex:
            present_error(self._parent, ex)
            return False

    def delete_cita(self, cita_id: int) -> bool:
        if cita_id <= 0:
            return False

        res = QMessageBox.question(
            self._parent,
            "Eliminar cita",
            "¿Eliminar la cita seleccionada?\nEsta acción es irreversible.",
        )
        if res != QMessageBox.Yes:
            return False

        try:
            self._c.citas_repo.delete(cita_id)
            return True
        except Exception as e:
            present_error(self._parent, e)
            return False
