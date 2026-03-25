from __future__ import annotations

import ast
from pathlib import Path

RUTA_PAGE = Path("clinicdesk/app/pages/prediccion_ausencias/page.py")


def _clase_page() -> ast.ClassDef:
    tree = ast.parse(RUTA_PAGE.read_text(encoding="utf-8"))
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PagePrediccionAusencias")


def _metodo(nombre: str) -> ast.FunctionDef:
    clase = _clase_page()
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_page_no_importa_qthread_para_entrenamiento() -> None:
    tree = ast.parse(RUTA_PAGE.read_text(encoding="utf-8"))
    imports_qtcore = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "PySide6.QtCore"
    ]
    nombres = {alias.name for node in imports_qtcore for alias in node.names}
    assert "QThread" not in nombres


def test_page_entrenamiento_llama_coordinador_premium() -> None:
    metodo = _metodo("_iniciar_entrenamiento_premium")
    llamadas = [
        nodo
        for nodo in ast.walk(metodo)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "iniciar"
    ]
    assert len(llamadas) == 1


def test_page_ya_no_tiene_atributos_thread_local_entrenamiento() -> None:
    init = _metodo("__init__")
    atributos = [
        nodo.target.attr
        for nodo in ast.walk(init)
        if isinstance(nodo, ast.AnnAssign)
        and isinstance(nodo.target, ast.Attribute)
        and isinstance(nodo.target.value, ast.Name)
        and nodo.target.value.id == "self"
    ]
    assert "_entrenar_thread" not in atributos
    assert "_entrenar_worker" not in atributos
