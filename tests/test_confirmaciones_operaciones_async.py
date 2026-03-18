from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication, QWidget
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.usecases.recordatorios_citas import ResultadoLoteRecordatoriosDTO
from clinicdesk.app.pages.confirmaciones.acciones_rapidas_confirmaciones import (
    on_whatsapp_rapido_fail,
    on_whatsapp_rapido_ok,
)
from clinicdesk.app.pages.confirmaciones.lote_controller import GestorLoteConfirmaciones

RUTA_ACCIONES_RAPIDAS = Path("clinicdesk/app/pages/confirmaciones/acciones_rapidas_confirmaciones.py")
RUTA_LOTE_CONTROLLER = Path("clinicdesk/app/pages/confirmaciones/lote_controller.py")


class _I18nFalso:
    def t(self, key: str) -> str:
        return key


class _PageFalsa:
    def __init__(self) -> None:
        self._coordinador_contexto = type("Ctx", (), {"nueva_operacion_whatsapp_rapido": lambda self: 10})()
        self._token_whatsapp_rapido = 10
        self._cita_en_preparacion = 25
        self.telemetria: list[tuple[str, str, int | None]] = []
        self.refreshes: list[tuple[str, int]] = []
        self.feedback_permitido = True
        self._i18n = _I18nFalso()

    def _es_whatsapp_rapido_vigente(self, operation_id: int) -> bool:
        return operation_id == self._token_whatsapp_rapido

    def _registrar_telemetria(self, evento: str, resultado: str, cita_id: int | None) -> None:
        self.telemetria.append((evento, resultado, cita_id))

    def _solicitar_refresh_operativo(self, *, origen: str, operation_id: int) -> None:
        self.refreshes.append((origen, operation_id))

    def _puede_mostrar_feedback_operativo(self, _operation_id: int) -> bool:
        return self.feedback_permitido


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_whatsapp_rapido_ok_descarta_resultado_tardio(monkeypatch: pytest.MonkeyPatch) -> None:
    page = _PageFalsa()
    mensajes: list[str] = []
    monkeypatch.setattr(
        "clinicdesk.app.pages.confirmaciones.acciones_rapidas_confirmaciones.QMessageBox.information",
        lambda *_args: mensajes.append("ok"),
    )

    on_whatsapp_rapido_ok(page, 9)

    assert page.telemetria == []
    assert page.refreshes == []
    assert mensajes == []


def test_whatsapp_rapido_fail_tardio_no_muestra_feedback(monkeypatch: pytest.MonkeyPatch) -> None:
    page = _PageFalsa()
    page.feedback_permitido = False
    warnings: list[str] = []
    monkeypatch.setattr(
        "clinicdesk.app.pages.confirmaciones.acciones_rapidas_confirmaciones.QMessageBox.warning",
        lambda *_args: warnings.append("warning"),
    )

    on_whatsapp_rapido_fail(page, "confirmaciones.lote.error_accionable", 10)

    assert page.telemetria == [("confirmaciones_whatsapp_rapido", "fail", 25)]
    assert page.refreshes == [("whatsapp_rapido_fail", 10)]
    assert warnings == []


def test_lote_ok_vigente_refresca_una_vez(monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    refrescos: list[int] = []
    parent = QWidget()
    controller = GestorLoteConfirmaciones(
        parent,
        _I18nFalso(),
        facade=object(),
        selected_ids=lambda: (1, 2),
        on_done=lambda operation_id: refrescos.append(operation_id),
        contexto_vigente=lambda: True,
    )
    controller._operacion_actual = 3

    monkeypatch.setattr(
        "clinicdesk.app.pages.confirmaciones.lote_controller.QMessageBox.information",
        lambda *_args: None,
    )

    dto = ResultadoLoteRecordatoriosDTO(preparadas=2)
    controller._on_ok(dto, 3)
    controller._on_ok(dto, 3)

    assert refrescos == [3]


def test_lote_omite_resultado_si_contexto_no_vigente(monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    refrescos: list[int] = []
    parent = QWidget()
    controller = GestorLoteConfirmaciones(
        parent,
        _I18nFalso(),
        facade=object(),
        selected_ids=lambda: (1,),
        on_done=lambda operation_id: refrescos.append(operation_id),
        contexto_vigente=lambda: False,
    )
    controller._operacion_actual = 7
    avisos: list[str] = []

    monkeypatch.setattr(
        "clinicdesk.app.pages.confirmaciones.lote_controller.QMessageBox.warning",
        lambda *_args: avisos.append("warning"),
    )

    controller._on_fail("confirmaciones.lote.error_accionable", 7)

    assert refrescos == []
    assert avisos == []


def test_worker_wiring_sin_callbacks_directos_a_ui() -> None:
    tree_lote = ast.parse(RUTA_LOTE_CONTROLLER.read_text(encoding="utf-8"))
    metodo_lote = next(
        node for node in ast.walk(tree_lote) if isinstance(node, ast.FunctionDef) and node.name == "_arrancar_worker"
    )
    llamadas_lote = [
        node
        for node in ast.walk(metodo_lote)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "arrancar_worker_lote"
    ]
    assert len(llamadas_lote) == 1
    kwargs_lote = {kw.arg: kw.value for kw in llamadas_lote[0].keywords if kw.arg is not None}
    assert isinstance(kwargs_lote["on_ok"], ast.Attribute)
    assert kwargs_lote["on_ok"].attr == "_on_ok"
    assert isinstance(kwargs_lote["on_error"], ast.Attribute)
    assert kwargs_lote["on_error"].attr == "_on_fail"

    tree_rapido = ast.parse(RUTA_ACCIONES_RAPIDAS.read_text(encoding="utf-8"))
    metodo_rapido = next(
        node
        for node in ast.walk(tree_rapido)
        if isinstance(node, ast.FunctionDef) and node.name == "preparar_whatsapp_rapido"
    )
    llamadas_rapido = [
        node
        for node in ast.walk(metodo_rapido)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "arrancar_preparacion_whatsapp"
    ]
    assert len(llamadas_rapido) == 1
    asignacion_operacion = next(
        node
        for node in metodo_rapido.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "operation_id" for target in node.targets)
    )
    assert isinstance(asignacion_operacion.value, ast.Call)
    assert isinstance(asignacion_operacion.value.func, ast.Attribute)
    assert asignacion_operacion.value.func.attr == "nueva_operacion_whatsapp_rapido"

    kwargs_rapido = {kw.arg: kw.value for kw in llamadas_rapido[0].keywords if kw.arg is not None}
    assert isinstance(kwargs_rapido["on_ok"], ast.Attribute)
    assert kwargs_rapido["on_ok"].attr == "_on_whatsapp_rapido_ok"
    assert isinstance(kwargs_rapido["on_error"], ast.Attribute)
    assert kwargs_rapido["on_error"].attr == "_on_whatsapp_rapido_fail"
