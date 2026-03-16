from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.confirmaciones.dtos import ResultadoConfirmacionesDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.confirmaciones.page import PageConfirmaciones
from clinicdesk.app.pages.confirmaciones.workers_confirmaciones import RelayConfirmaciones

RUTA_PAGE = Path("clinicdesk/app/pages/confirmaciones/page.py")


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _obtener_metodo(nombre: str) -> ast.FunctionDef:
    source = RUTA_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    clase = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PageConfirmaciones")
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_relay_carga_ok_propaga_payload_con_token() -> None:
    relay = RelayConfirmaciones(token=77)
    recibido: list[tuple[object, int]] = []
    relay.carga_ok.connect(lambda payload, token: recibido.append((payload, token)))

    payload = {"ok": True}
    relay.on_worker_carga_ok(payload)

    assert recibido == [(payload, 77)]


def test_on_carga_ok_descarta_resultado_obsoleto(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = PageConfirmaciones(container, I18nManager("es"))
    page._pagina_visible = True
    page._token_carga = 5

    llamado = {"ok": False}
    monkeypatch.setattr(page._vm, "resolver_carga_ok", lambda **_kwargs: llamado.__setitem__("ok", True))

    page._on_carga_ok(ResultadoConfirmacionesDTO(total=1, mostrados=1, items=[], salud_prediccion=None), 4)

    assert llamado["ok"] is False


def test_on_carga_error_vigente_no_rompe_pagina(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = PageConfirmaciones(container, I18nManager("es"))
    page._pagina_visible = True
    page._token_carga = 9

    llamado = {"error": False}
    monkeypatch.setattr(page._vm, "resolver_carga_error", lambda **_kwargs: llamado.__setitem__("error", True))

    page._on_carga_error("RuntimeError", 9)

    assert llamado["error"] is True


def test_on_carga_ok_omite_render_si_pagina_no_visible(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = PageConfirmaciones(container, I18nManager("es"))
    page._pagina_visible = False
    page._token_carga = 3

    llamado = {"ok": False}
    monkeypatch.setattr(page._vm, "resolver_carga_ok", lambda **_kwargs: llamado.__setitem__("ok", True))

    page._on_carga_ok(ResultadoConfirmacionesDTO(total=1, mostrados=1, items=[], salud_prediccion=None), 3)

    assert llamado["ok"] is False


def test_busqueda_rapida_usa_slots_explicitos_sin_lambdas() -> None:
    metodo = _obtener_metodo("buscar_rapido_async")
    llamadas = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "arrancar_busqueda_rapida"
    ]
    assert len(llamadas) == 1

    kwargs = {kw.arg: kw.value for kw in llamadas[0].keywords if kw.arg is not None}
    assert isinstance(kwargs["on_payload"], ast.Attribute)
    assert kwargs["on_payload"].attr == "_on_busqueda_rapida_ok"
    assert isinstance(kwargs["on_error"], ast.Attribute)
    assert kwargs["on_error"].attr == "_on_busqueda_rapida_error"
    assert isinstance(kwargs["on_thread_finished"], ast.Attribute)
    assert kwargs["on_thread_finished"].attr == "_on_busqueda_rapida_thread_finished"


def test_arrancar_carga_usa_slots_explicitos_sin_lambdas() -> None:
    metodo = _obtener_metodo("_arrancar_worker_carga")
    llamadas = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "arrancar_carga"
    ]
    assert len(llamadas) == 1

    kwargs = {kw.arg: kw.value for kw in llamadas[0].keywords if kw.arg is not None}
    assert isinstance(kwargs["on_ok"], ast.Attribute)
    assert kwargs["on_ok"].attr == "_on_carga_ok"
    assert isinstance(kwargs["on_error"], ast.Attribute)
    assert kwargs["on_error"].attr == "_on_carga_error"
    assert isinstance(kwargs["on_thread_finished"], ast.Attribute)
    assert kwargs["on_thread_finished"].attr == "_on_carga_thread_finished"
