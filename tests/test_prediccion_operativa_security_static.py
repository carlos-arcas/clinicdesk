from __future__ import annotations

import ast
from pathlib import Path

RUTA_PAGE = Path("clinicdesk/app/pages/prediccion_operativa/page.py")
RUTA_REGISTER = Path("clinicdesk/app/pages/prediccion_operativa/register.py")


def _metodo(nombre: str) -> ast.FunctionDef:
    tree = ast.parse(RUTA_PAGE.read_text(encoding="utf-8"))
    clase = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PagePrediccionOperativa"
    )
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_entrenar_aplica_guardrail_antes_de_iniciar_background() -> None:
    metodo = _metodo("_entrenar")
    nombres_llamados = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    ]

    assert "_autorizar_entrenamiento" in nombres_llamados
    assert "_iniciar_entrenamiento_background" in nombres_llamados


def test_guardrail_denegado_registra_telemetria_y_feedback() -> None:
    metodo = _metodo("_autorizar_entrenamiento")
    nombres_llamados = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    ]

    assert "_mostrar_feedback_denegacion" in nombres_llamados
    assert "_registrar_telemetria" in nombres_llamados


def test_register_inyecta_autorizador_existente_del_container() -> None:
    tree = ast.parse(RUTA_REGISTER.read_text(encoding="utf-8"))
    atributos = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "container"
    }

    assert "autorizador_acciones" in atributos
