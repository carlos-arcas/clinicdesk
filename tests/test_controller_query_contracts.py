from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

qtwidgets = types.ModuleType("PySide6.QtWidgets")


class _QDialog:
    Accepted = 1


class _QWidget:
    pass


qtwidgets.QDialog = _QDialog
qtwidgets.QWidget = _QWidget
pyside6 = types.ModuleType("PySide6")
pyside6.QtWidgets = qtwidgets
sys.modules.setdefault("PySide6", pyside6)
sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)

mod_dialog_dispensar = types.ModuleType("clinicdesk.app.pages.dialog_dispensar")
mod_dialog_dispensar.DispensarDialog = object
sys.modules.setdefault("clinicdesk.app.pages.dialog_dispensar", mod_dialog_dispensar)

mod_dialog_override = types.ModuleType("clinicdesk.app.pages.dialog_override")
mod_dialog_override.OverrideDialog = object
sys.modules.setdefault("clinicdesk.app.pages.dialog_override", mod_dialog_override)

mod_error_presenter = types.ModuleType("clinicdesk.app.ui.error_presenter")
mod_error_presenter.present_error = lambda *_args, **_kwargs: None
sys.modules.setdefault("clinicdesk.app.ui.error_presenter", mod_error_presenter)

from clinicdesk.app.controllers.farmacia_controller import FarmaciaController
from clinicdesk.app.controllers.incidencias_controller import IncidenciasController
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia
from clinicdesk.app.queries.farmacia_queries import FarmaciaQueries, RecetaLineaRow, RecetaRow
from clinicdesk.app.queries.incidencias_queries import IncidenciasQueries


def _build_dispensar_dialog_stub(personal_id: int):
    class _DispensarDialogStub:
        def __init__(self, _parent, *, container) -> None:
            del container
            self._data = SimpleNamespace(personal_id=personal_id, cantidad=2)

        def exec(self) -> int:
            return _QDialog.Accepted

        def get_data(self):
            return self._data

    return _DispensarDialogStub


class _UseCaseRecorder:
    last_request = None

    def __init__(self, _container) -> None:
        pass

    def execute(self, req) -> None:
        type(self).last_request = req


@pytest.fixture(autouse=True)
def _reset_use_case_recorder() -> None:
    _UseCaseRecorder.last_request = None


def test_farmacia_controller_lista_recetas_y_lineas_con_query_alineada(container, seed_data) -> None:
    controller = FarmaciaController(parent=None, container=container)

    recetas = controller.list_recetas_by_paciente(seed_data["paciente_activo_id"])
    assert recetas
    receta = recetas[0]
    assert isinstance(receta, RecetaRow)

    lineas = controller.list_lineas_by_receta(receta.id)
    assert lineas
    linea = lineas[0]
    assert isinstance(linea, RecetaLineaRow)
    assert linea.medicamento_id == seed_data["medicamento_activo_id"]


def test_farmacia_controller_dispensar_flow_envia_medicamento_id_real(monkeypatch, container, seed_data) -> None:
    controller = FarmaciaController(parent=None, container=container)
    receta = controller.list_recetas_by_paciente(seed_data["paciente_activo_id"])[0]
    linea = controller.list_lineas_by_receta(receta.id)[0]

    monkeypatch.setattr(
        "clinicdesk.app.controllers.farmacia_controller.DispensarDialog",
        _build_dispensar_dialog_stub(seed_data["personal_activo_id"]),
    )
    monkeypatch.setattr("clinicdesk.app.controllers.farmacia_controller.DispensarMedicamentoUseCase", _UseCaseRecorder)
    controller._uc = _UseCaseRecorder(container)

    assert controller.dispensar_flow(seed_data["paciente_activo_id"], receta, linea) is True
    assert _UseCaseRecorder.last_request is not None
    assert _UseCaseRecorder.last_request.medicamento_id == linea.medicamento_id


def test_incidencias_controller_usa_connection_para_queries(container, seed_data) -> None:
    controller = IncidenciasController(parent=None, container=container)
    container.incidencias_repo.create(
        Incidencia(
            tipo="CITA",
            severidad="ALTA",
            estado="ABIERTA",
            fecha_hora="2024-05-20 11:00:00",
            descripcion="Incidencia controller",
            medico_id=seed_data["medico_activo_id"],
            personal_id=seed_data["personal_activo_id"],
            cita_id=None,
            dispensacion_id=None,
            receta_id=None,
            confirmado_por_personal_id=seed_data["personal_activo_id"],
            nota_override="Aprobada",
        )
    )

    resultados = controller.search(
        tipo="CITA",
        estado=None,
        severidad=None,
        fecha_desde=None,
        fecha_hasta=None,
    )

    assert isinstance(controller._q, IncidenciasQueries)
    assert controller._q._conn is container.connection
    assert resultados


def test_controladores_queries_lectura_usan_dependencia_correcta(monkeypatch, container) -> None:
    capturas: dict[str, object] = {}

    class FarmaciaQueriesSpy(FarmaciaQueries):
        def __init__(self, connection) -> None:
            capturas["farmacia_connection"] = connection
            super().__init__(connection)

    class IncidenciasQueriesSpy(IncidenciasQueries):
        def __init__(self, connection) -> None:
            capturas["incidencias_connection"] = connection
            super().__init__(connection)

    monkeypatch.setattr("clinicdesk.app.controllers.farmacia_controller.FarmaciaQueries", FarmaciaQueriesSpy)
    monkeypatch.setattr("clinicdesk.app.controllers.incidencias_controller.IncidenciasQueries", IncidenciasQueriesSpy)

    FarmaciaController(parent=None, container=container)
    IncidenciasController(parent=None, container=container)

    assert capturas == {
        "farmacia_connection": container.connection,
        "incidencias_connection": container.connection,
    }
