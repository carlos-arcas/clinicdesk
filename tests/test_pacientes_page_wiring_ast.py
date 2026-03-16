from __future__ import annotations

import ast
from pathlib import Path


def test_busqueda_rapida_pacientes_usa_slots_explicitos_sin_lambdas() -> None:
    source = Path("clinicdesk/app/pages/pacientes/page.py").read_text(encoding="utf-8")
    arbol = ast.parse(source)
    llamadas = [
        node
        for node in ast.walk(arbol)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "arrancar_busqueda_rapida"
    ]
    assert llamadas, "No se encontró llamada a arrancar_busqueda_rapida"
    llamada = llamadas[0]
    kwargs = {kw.arg: kw.value for kw in llamada.keywords if kw.arg}

    assert isinstance(kwargs["on_payload"], ast.Attribute)
    assert kwargs["on_payload"].attr == "_on_busqueda_rapida_ok"
    assert isinstance(kwargs["on_error"], ast.Attribute)
    assert kwargs["on_error"].attr == "_on_busqueda_rapida_error"
    assert isinstance(kwargs["on_thread_finished"], ast.Attribute)
    assert kwargs["on_thread_finished"].attr == "_on_busqueda_rapida_thread_finished"
