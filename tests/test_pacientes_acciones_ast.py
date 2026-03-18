from __future__ import annotations

import ast
from pathlib import Path


RUTA_ACCIONES = Path("clinicdesk/app/pages/pacientes/acciones_pacientes.py")


def _funcion(nombre: str) -> ast.FunctionDef:
    tree = ast.parse(RUTA_ACCIONES.read_text(encoding="utf-8"))
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_on_historial_registra_auditoria_y_abre_dialogo() -> None:
    funcion = _funcion("on_historial")
    atributos = {
        node.func.attr
        for node in ast.walk(funcion)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    nombres = {
        node.func.id for node in ast.walk(funcion) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "execute" in atributos
    assert "HistorialPacienteDialog" in nombres


def test_open_context_menu_delega_dispatch_centralizado() -> None:
    funcion = _funcion("open_context_menu")
    nombres = [
        node.func.id for node in ast.walk(funcion) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]

    assert "_resolver_accion_menu_contextual" in nombres
    assert "despachar_accion" in nombres
