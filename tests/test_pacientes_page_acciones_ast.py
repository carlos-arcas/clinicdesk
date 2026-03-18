from __future__ import annotations

import ast
from pathlib import Path


RUTA_PAGE = Path("clinicdesk/app/pages/pacientes/page.py")


def _metodo(nombre: str) -> ast.FunctionDef:
    tree = ast.parse(RUTA_PAGE.read_text(encoding="utf-8"))
    clase = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PagePacientes")
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_page_pacientes_delega_botones_en_coordinador() -> None:
    metodo = _metodo("_update_buttons")
    llamadas = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "actualizar_botones"
    ]
    assert len(llamadas) == 1
    assert isinstance(llamadas[0].func.value, ast.Attribute)
    assert llamadas[0].func.value.attr == "_coordinador_seleccion_acciones"


def test_page_pacientes_prepara_estado_antes_de_menu_contextual() -> None:
    metodo = _metodo("_open_context_menu")
    llamadas = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "preparar_context_menu"
    ]
    assert len(llamadas) == 1
