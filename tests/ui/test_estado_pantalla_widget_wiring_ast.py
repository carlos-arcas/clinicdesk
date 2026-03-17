from __future__ import annotations

import ast
from pathlib import Path


RUTA = Path("clinicdesk/app/ui/widgets/estado_pantalla_widget.py")


def test_senales_estado_pantalla_usan_queued_connection() -> None:
    tree = ast.parse(RUTA.read_text(encoding="utf-8"))
    clase = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "EstadoPantallaWidget")
    init = next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    connects = [
        node
        for node in ast.walk(init)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "connect"
        and node.args
    ]
    objetivos = {"solicitar_loading", "solicitar_empty", "solicitar_error", "solicitar_processing", "solicitar_content"}
    hallados: set[str] = set()
    for call in connects:
        base = call.func.value
        if not isinstance(base, ast.Attribute) or not isinstance(base.value, ast.Name) or base.value.id != "self":
            continue
        if base.attr not in objetivos:
            continue
        assert len(call.args) == 2
        modo = call.args[1]
        assert isinstance(modo, ast.Attribute)
        assert modo.attr == "QueuedConnection"
        hallados.add(base.attr)
    assert hallados == objetivos
