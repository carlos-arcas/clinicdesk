from __future__ import annotations

from dataclasses import dataclass, replace
import sys
import types
from typing import Any

qtwidgets = types.ModuleType("PySide6.QtWidgets")
qtwidgets.QWidget = object
qtwidgets.QDialog = type("QDialog", (), {"Accepted": 1})
pyside6 = types.ModuleType("PySide6")
pyside6.QtWidgets = qtwidgets
sys.modules.setdefault("PySide6", pyside6)
sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)


dialog_dispensar = types.ModuleType("clinicdesk.app.pages.dialog_dispensar")
dialog_override = types.ModuleType("clinicdesk.app.pages.dialog_override")
error_presenter = types.ModuleType("clinicdesk.app.ui.error_presenter")


@dataclass(slots=True)
class OverrideDecision:
    accepted: bool
    nota_override: str | None
    confirmado_por_personal_id: int | None


class _PlaceholderDialog:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def exec(self) -> int:
        return 0


class _PlaceholderOverride(_PlaceholderDialog):
    def get_decision(self) -> OverrideDecision:
        return OverrideDecision(False, None, None)


dialog_dispensar.DispensarDialog = _PlaceholderDialog
dialog_override.OverrideDialog = _PlaceholderOverride
dialog_override.OverrideDecision = OverrideDecision
error_presenter.present_error = lambda *_args, **_kwargs: None

sys.modules.setdefault("clinicdesk.app.pages.dialog_dispensar", dialog_dispensar)
sys.modules.setdefault("clinicdesk.app.pages.dialog_override", dialog_override)
sys.modules.setdefault("clinicdesk.app.ui.error_presenter", error_presenter)

from clinicdesk.app.application.usecases.dispensar_medicamento import PendingWarningsError, WarningItem
from clinicdesk.app.controllers.farmacia_controller import FarmaciaController
from clinicdesk.app.controllers.incidencias_controller import IncidenciasController
from clinicdesk.app.queries.farmacia_queries import RecetaLineaRow, RecetaRow


@dataclass
class _DispensarData:
    cantidad: int
    personal_id: int


class _DialogoAceptado:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self._data = _DispensarData(cantidad=2, personal_id=17)

    def exec(self) -> int:
        return 1

    def get_data(self) -> _DispensarData:
        return self._data


class _OverrideAceptado:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self._decision = OverrideDecision(
            accepted=True,
            nota_override="Aprobado por guardia",
            confirmado_por_personal_id=99,
        )

    def exec(self) -> int:
        return 1

    def get_decision(self) -> OverrideDecision:
        return self._decision


class _UseCaseSpy:
    def __init__(self, _container: Any) -> None:
        self.requests: list[Any] = []

    def execute(self, request: Any) -> None:
        self.requests.append(replace(request))


class _UseCaseConWarning:
    def __init__(self, _container: Any) -> None:
        self.requests: list[Any] = []
        self._first_call = True

    def execute(self, request: Any) -> None:
        self.requests.append(replace(request))
        if self._first_call:
            self._first_call = False
            raise PendingWarningsError([WarningItem(codigo="TEST", mensaje="warning", severidad="MEDIA")])


def test_farmacia_controller_usa_conexion_y_metodos_canonicamente(container, seed_data) -> None:
    controller = FarmaciaController(parent=None, container=container)

    recetas = controller.recetas_por_paciente(seed_data["paciente_activo_id"])

    assert recetas
    assert recetas[0].id == seed_data["receta_id"]

    lineas = controller.lineas_por_receta(seed_data["receta_id"])

    assert lineas
    assert lineas[0].id == seed_data["receta_linea_id"]
    assert not hasattr(lineas[0], "medicamento_id")


def test_farmacia_controller_dispensar_flow_delega_medicamento_en_usecase(monkeypatch, container) -> None:
    receta = RecetaRow(id=10, fecha="2025-01-01", medico="Dra. Uno", estado="ACTIVA")
    linea = RecetaLineaRow(id=20, medicamento="Amoxil", dosis="1/8h", cantidad=10, pendiente=5, estado="PENDIENTE")
    usecase = _UseCaseSpy(container)

    monkeypatch.setattr("clinicdesk.app.controllers.farmacia_controller.DispensarDialog", _DialogoAceptado)
    monkeypatch.setattr("clinicdesk.app.controllers.farmacia_controller.DispensarMedicamentoUseCase", lambda c: usecase)

    controller = FarmaciaController(parent=None, container=container)

    assert controller.dispensar_flow(paciente_id=1, receta=receta, linea=linea) is True
    assert len(usecase.requests) == 1
    request = usecase.requests[0]
    assert request.receta_id == 10
    assert request.receta_linea_id == 20
    assert request.personal_id == 17
    assert request.cantidad == 2
    assert request.medicamento_id is None


def test_farmacia_controller_dispensar_flow_reintenta_con_override(monkeypatch, container) -> None:
    receta = RecetaRow(id=10, fecha="2025-01-01", medico="Dra. Uno", estado="ACTIVA")
    linea = RecetaLineaRow(id=20, medicamento="Amoxil", dosis="1/8h", cantidad=10, pendiente=5, estado="PENDIENTE")
    usecase = _UseCaseConWarning(container)

    monkeypatch.setattr("clinicdesk.app.controllers.farmacia_controller.DispensarDialog", _DialogoAceptado)
    monkeypatch.setattr("clinicdesk.app.controllers.farmacia_controller.OverrideDialog", _OverrideAceptado)
    monkeypatch.setattr("clinicdesk.app.controllers.farmacia_controller.DispensarMedicamentoUseCase", lambda c: usecase)

    controller = FarmaciaController(parent=None, container=container)

    assert controller.dispensar_flow(paciente_id=1, receta=receta, linea=linea) is True
    assert len(usecase.requests) == 2
    primer_intento, segundo_intento = usecase.requests
    assert primer_intento.override is False
    assert segundo_intento.override is True
    assert segundo_intento.nota_override == "Aprobado por guardia"
    assert segundo_intento.confirmado_por_personal_id == 99
    assert segundo_intento.medicamento_id is None


def test_incidencias_controller_usa_conexion_y_queries_correctas(container) -> None:
    controller = IncidenciasController(parent=None, container=container)

    resultados = controller.search(
        tipo="DISPENSACION",
        estado=None,
        severidad=None,
        fecha_desde=None,
        fecha_hasta=None,
    )

    detalle = controller.get_detail(1)

    assert resultados == []
    assert detalle is None
    assert controller._q._conn is container.connection
