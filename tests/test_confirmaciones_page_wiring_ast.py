from __future__ import annotations

import ast
from pathlib import Path

RUTA_PAGE = Path("clinicdesk/app/pages/confirmaciones/page.py")


def _obtener_metodo(nombre: str) -> ast.FunctionDef:
    source = RUTA_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    clase = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PageConfirmaciones")
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


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


def test_on_estado_vm_omite_render_cuando_pagina_no_visible() -> None:
    metodo = _obtener_metodo("_on_estado_vm")
    primer_if = next((node for node in metodo.body if isinstance(node, ast.If)), None)
    assert isinstance(primer_if, ast.If)
    assert isinstance(primer_if.test, ast.UnaryOp)
    assert isinstance(primer_if.test.op, ast.Not)
    assert isinstance(primer_if.test.operand, ast.Attribute)
    assert primer_if.test.operand.attr == "pagina_visible"
