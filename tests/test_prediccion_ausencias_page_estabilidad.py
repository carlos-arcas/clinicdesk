from __future__ import annotations

import ast
from pathlib import Path

RUTA_PAGE = Path("clinicdesk/app/pages/prediccion_ausencias/page.py")


def _obtener_metodo(nombre: str) -> ast.FunctionDef:
    source = RUTA_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    clase = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PagePrediccionAusencias"
    )
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_cambio_periodo_programa_callback_diferido_dedicado() -> None:
    metodo = _obtener_metodo("_on_cambio_periodo_resultados")
    llamadas = [
        nodo
        for nodo in ast.walk(metodo)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "_programar_actualizacion_resultados_recientes"
    ]
    assert len(llamadas) == 1


def test_programador_usa_single_shot_con_callback_nombrado() -> None:
    metodo = _obtener_metodo("_programar_actualizacion_resultados_recientes")
    single_shots = [
        nodo
        for nodo in ast.walk(metodo)
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "singleShot"
    ]
    assert len(single_shots) == 1
    assert isinstance(single_shots[0].args[1], ast.Name)
    assert single_shots[0].args[1].id == "ejecutar"


def test_actualizacion_diferida_verifica_vigencia_antes_de_renderizar() -> None:
    metodo = _obtener_metodo("_actualizar_resultados_recientes_diferido")
    condiciones = [
        nodo
        for nodo in ast.walk(metodo)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "_es_actualizacion_resultados_vigente"
    ]
    assert len(condiciones) == 1


def test_guardia_vigencia_valida_token_y_visibilidad() -> None:
    metodo = _obtener_metodo("_es_actualizacion_resultados_vigente")
    attrs = [n.attr for n in ast.walk(metodo) if isinstance(n, ast.Attribute)]
    assert "_token_resultados_diferidos" in attrs
    assert "_token_resultados_vigente" in attrs
    assert "_pagina_visible" in attrs


def test_on_hide_invalida_contexto_diferido() -> None:
    metodo = _obtener_metodo("on_hide")
    incrementos = [
        nodo
        for nodo in ast.walk(metodo)
        if isinstance(nodo, ast.AugAssign)
        and isinstance(nodo.target, ast.Attribute)
        and nodo.target.attr == "_token_resultados_vigente"
    ]
    assert len(incrementos) == 1


def test_resumen_modelo_usa_contrato_explicito_del_facade() -> None:
    metodo = _obtener_metodo("_actualizar_resumen_modelo")
    attrs = [n.attr for n in ast.walk(metodo) if isinstance(n, ast.Attribute)]
    assert "obtener_resumen_ultimo_entrenamiento_uc" in attrs
    assert "cargar_metadata" not in attrs


def test_historial_modelo_usa_contrato_explicito_del_facade() -> None:
    metodo = _obtener_metodo("_actualizar_historial_entrenamientos")
    attrs = [n.attr for n in ast.walk(metodo) if isinstance(n, ast.Attribute)]
    assert "obtener_historial_entrenamientos_uc" in attrs
    assert "cargar_historial" not in attrs
