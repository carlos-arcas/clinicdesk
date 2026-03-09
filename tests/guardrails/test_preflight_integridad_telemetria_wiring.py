from __future__ import annotations

import ast
from pathlib import Path


class _CallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.faltantes: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        nombre = None
        if isinstance(node.func, ast.Name):
            nombre = node.func.id
        elif isinstance(node.func, ast.Attribute):
            nombre = node.func.attr

        if nombre == "ObtenerResumenTelemetriaSemana":
            tiene_verificador = any(keyword.arg == "verificador_integridad" for keyword in node.keywords)
            if not tiene_verificador:
                self.faltantes.append(f"{nombre} sin verificador_integridad en línea {node.lineno}")

        self.generic_visit(node)


def _calls_sin_verificador(ruta: Path) -> list[str]:
    tree = ast.parse(ruta.read_text(encoding="utf-8"))
    visitor = _CallVisitor()
    visitor.visit(tree)
    return visitor.faltantes


def test_page_gestion_inyecta_preflight_integridad_en_resumen_telemetria() -> None:
    ruta = Path("clinicdesk/app/pages/gestion/page.py")
    contenido = ruta.read_text(encoding="utf-8")

    assert "ObtenerResumenTelemetriaSemana(" in contenido
    assert "verificador_integridad=self._queries_telemetria" in contenido


def test_usecase_resumen_telemetria_exige_verificador_integridad_en_call_sites() -> None:
    rutas = sorted(Path("clinicdesk/app").rglob("*.py"))
    faltantes: list[str] = []
    for ruta in rutas:
        faltantes.extend(f"{ruta}: {err}" for err in _calls_sin_verificador(ruta))

    assert not faltantes, "Faltan inyecciones de verificador_integridad en resumen telemetría:\n" + "\n".join(faltantes)
