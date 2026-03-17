from __future__ import annotations

import ast
from pathlib import Path

RUTA = Path("clinicdesk/app/ui/jobs/job_manager.py")


def _metodo(nombre: str) -> ast.FunctionDef:
    tree = ast.parse(RUTA.read_text(encoding="utf-8"))
    clase = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "JobManager")
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_run_job_no_usa_lambdas_para_routing_critico() -> None:
    metodo = _metodo("run_job")
    lambda_connects = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "connect"
        and node.args
        and isinstance(node.args[0], ast.Lambda)
    ]
    assert lambda_connects == []
