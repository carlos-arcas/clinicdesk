from __future__ import annotations

import ast
from pathlib import Path


RUTA_MAIN_WINDOW = Path("clinicdesk/app/ui/main_window.py")


def _obtener_metodo_restaurar_pagina_ultima() -> ast.FunctionDef:
    source = RUTA_MAIN_WINDOW.read_text(encoding="utf-8")
    tree = ast.parse(source)
    clase_main_window = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "MainWindow")
    return next(
        node
        for node in clase_main_window.body
        if isinstance(node, ast.FunctionDef) and node.name == "_restaurar_pagina_ultima"
    )


def test_arranque_define_pacientes_como_pagina_por_defecto() -> None:
    metodo = _obtener_metodo_restaurar_pagina_ultima()

    assert any(
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "key"
        and isinstance(node.value, ast.Constant)
        and node.value.value == "pacientes"
        for node in metodo.body
    )


def test_arranque_restaura_ultima_pagina_solo_con_preferencia_explicita() -> None:
    metodo = _obtener_metodo_restaurar_pagina_ultima()

    assert any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.BoolOp)
        and isinstance(node.test.op, ast.And)
        and any(
            isinstance(valor, ast.Attribute) and valor.attr == "restaurar_pagina_ultima_en_arranque"
            for valor in node.test.values
        )
        for node in metodo.body
    )


def test_arranque_no_fuerza_confirmaciones_como_default() -> None:
    metodo = _obtener_metodo_restaurar_pagina_ultima()

    assert not any(
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "key"
        and isinstance(node.value, ast.Constant)
        and node.value.value == "confirmaciones"
        for node in metodo.body
    )
