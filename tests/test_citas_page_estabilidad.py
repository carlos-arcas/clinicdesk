from __future__ import annotations

import ast
from pathlib import Path

RUTA_PAGE = Path("clinicdesk/app/pages/citas/page.py")


def _obtener_metodo(nombre: str) -> ast.FunctionDef:
    source = RUTA_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    clase = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PageCitas")
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_programar_refresco_lista_usa_callback_dedicado_con_token() -> None:
    metodo = _obtener_metodo("_programar_refresco_lista")
    llamadas = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "singleShot"
    ]
    assert len(llamadas) == 1
    assert isinstance(llamadas[0].args[1], ast.Name)
    assert llamadas[0].args[1].id == "ejecutar"


def test_resolver_intent_descarta_tokens_obsoletos() -> None:
    metodo = _obtener_metodo("_resolver_intent_navegacion")
    comparaciones = [
        nodo
        for nodo in ast.walk(metodo)
        if isinstance(nodo, ast.Compare)
        and isinstance(nodo.left, ast.Attribute)
        and nodo.left.attr == "_token_intent_pendiente"
    ]
    assert comparaciones
    assert any(
        isinstance(comp.comparators[0], ast.Attribute) and comp.comparators[0].attr == "_token_intent_navegacion"
        for comp in comparaciones
    )


def test_es_refresh_vigente_verifica_visibilidad_y_token() -> None:
    metodo = _obtener_metodo("_es_refresh_vigente")
    attrs = [n.attr for n in ast.walk(metodo) if isinstance(n, ast.Attribute)]
    assert "_pagina_visible" in attrs
    assert "_token_refresh_vigente" in attrs


def test_on_hide_invalida_refresh_vigente() -> None:
    metodo = _obtener_metodo("on_hide")
    llamadas = [
        node for node in ast.walk(metodo) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert any(llamada.func.attr == "_invalidar_refresh_vigente" for llamada in llamadas)
