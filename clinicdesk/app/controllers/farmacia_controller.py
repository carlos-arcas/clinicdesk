from __future__ import annotations

from typing import List

from PySide6.QtWidgets import QMessageBox, QWidget

from clinicdesk.app.container import AppContainer
from clinicdesk.app.queries.farmacia_queries import FarmaciaQueries, RecetaRow, RecetaLineaRow
from clinicdesk.app.application.usecases.dispensar_medicamento import (
    DispensarMedicamentoRequest,
    DispensarMedicamentoUseCase,
    PendingWarningsError,
)

from clinicdesk.app.pages.dialog_dispensar import DispensarDialog
from clinicdesk.app.pages.dialog_override import OverrideDialog


class FarmaciaController:
    """Controlador de Farmacia.

    - Lecturas vía queries (joins y proyecciones)
    - Escrituras vía usecase (dispensación + stock + auditoría)
    """

    def __init__(self, parent: QWidget, container: AppContainer) -> None:
        self._parent = parent
        self._c = container
        self._q = FarmaciaQueries(container)
        self._uc = DispensarMedicamentoUseCase(container)

    def list_recetas_by_paciente(self, paciente_id: int) -> List[RecetaRow]:
        return self._q.list_recetas_by_paciente(paciente_id)

    def list_lineas_by_receta(self, receta_id: int) -> List[RecetaLineaRow]:
        return self._q.list_lineas_by_receta(receta_id)

    def dispensar_flow(self, paciente_id: int, receta: RecetaRow, linea: RecetaLineaRow) -> bool:
        dlg = DispensarDialog(self._parent)
        if dlg.exec() != dlg.Accepted:
            return False

        data = dlg.get_data()
        if not data:
            return False

        req = DispensarMedicamentoRequest(
            receta_id=receta.id,
            receta_linea_id=linea.id,
            medicamento_id=linea.medicamento_id,
            personal_id=data.personal_id,
            cantidad=data.cantidad,
            override=False,
            nota_override=None,
            confirmado_por_personal_id=None,
        )

        try:
            self._uc.execute(req)
            return True

        except PendingWarningsError as e:
            od = OverrideDialog(self._parent, title="Confirmar dispensación con advertencias", warnings=e.warnings)
            if od.exec() != od.Accepted:
                return False

            decision = od.get_decision()
            if not decision.accepted:
                return False

            req.override = True
            req.nota_override = decision.nota_override
            req.confirmado_por_personal_id = decision.confirmado_por_personal_id

            self._uc.execute(req)
            return True

        except Exception as ex:
            QMessageBox.critical(self._parent, "Farmacia - Error", str(ex))
            return False
