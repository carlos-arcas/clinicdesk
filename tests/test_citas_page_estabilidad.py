from __future__ import annotations

import ast
from pathlib import Path

RUTA_PAGE = Path("clinicdesk/app/pages/citas/page.py")


def _obtener_clase_page() -> ast.ClassDef:
    source = RUTA_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PageCitas")


def _obtener_metodo(nombre: str) -> ast.FunctionDef:
    clase = _obtener_clase_page()
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


def test_resolver_intent_delega_en_coordinador_y_descarta_obsoletos() -> None:
    metodo = _obtener_metodo("_resolver_intent_navegacion")
    attrs = [n.attr for n in ast.walk(metodo) if isinstance(n, ast.Attribute)]
    assert "resolver_para_vista" in attrs
    assert "obsoleto" in attrs
    assert "limpiar_pendiente" in attrs


def test_es_refresh_vigente_consulta_estado_en_coordinador() -> None:
    metodo = _obtener_metodo("_es_refresh_vigente")
    attrs = [n.attr for n in ast.walk(metodo) if isinstance(n, ast.Attribute)]
    assert "pagina_visible" in attrs
    assert "token_vigente" in attrs


def test_on_hide_invalida_refresh_vigente() -> None:
    metodo = _obtener_metodo("on_hide")
    llamadas = [
        node for node in ast.walk(metodo) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert any(llamada.func.attr == "_invalidar_refresh_vigente" for llamada in llamadas)


def test_page_citas_declara_coordinadores_para_refresh_e_intents() -> None:
    clase = _obtener_clase_page()
    init = next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    asignaciones = [node for node in ast.walk(init) if isinstance(node, ast.Assign)]
    valores_por_destino: dict[str, str] = {}
    for asignacion in asignaciones:
        if len(asignacion.targets) != 1 or not isinstance(asignacion.targets[0], ast.Attribute):
            continue
        destino = asignacion.targets[0].attr
        valor = asignacion.value
        if isinstance(valor, ast.Call) and isinstance(valor.func, ast.Name):
            valores_por_destino[destino] = valor.func.id
    assert valores_por_destino.get("_coordinador_refresh") == "CoordinadorRefreshCitas"
    assert valores_por_destino.get("_coordinador_intents") == "CoordinadorIntentsCitas"
    assert valores_por_destino.get("_coordinador_banners") == "CoordinadorBannersCitas"
    assert valores_por_destino.get("_coordinador_salud_prediccion") == "CoordinadorSaludPrediccionCitas"


def test_actualizar_aviso_salud_prediccion_delega_en_coordinador() -> None:
    metodo = _obtener_metodo("_actualizar_aviso_salud_prediccion")
    attrs = [n.attr for n in ast.walk(metodo) if isinstance(n, ast.Attribute)]
    assert "estado_aviso_salud" in attrs
    assert "debe_loguear_aviso" in attrs
    assert "marcar_aviso_logueado" in attrs
