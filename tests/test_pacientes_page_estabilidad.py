from __future__ import annotations

import ast
from pathlib import Path


RUTA_PAGE = Path("clinicdesk/app/pages/pacientes/page.py")


def _obtener_metodo(nombre: str) -> ast.FunctionDef:
    source = RUTA_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    clase = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PagePacientes")
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_on_show_difiere_refresh_al_siguiente_tick() -> None:
    metodo = _obtener_metodo("on_show")
    llamadas = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_programar_refresh_on_show"
    ]
    assert llamadas

    llamadas_refresh_directo = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_refresh"
    ]
    assert not llamadas_refresh_directo


def test_on_estado_vm_omite_render_cuando_pagina_no_visible() -> None:
    metodo = _obtener_metodo("_on_estado_vm")
    primer_if = next((node for node in metodo.body if isinstance(node, ast.If)), None)
    assert isinstance(primer_if, ast.If)
    assert isinstance(primer_if.test, ast.UnaryOp)
    assert isinstance(primer_if.test.op, ast.Not)
    assert isinstance(primer_if.test.operand, ast.Attribute)
    assert primer_if.test.operand.attr == "_pagina_visible"
