from __future__ import annotations

import ast
from pathlib import Path

RUTA_PAGE_AUDITORIA = Path("clinicdesk/app/pages/auditoria/page.py")
RUTA_APP = Path("clinicdesk/app")


class _VisitorInstanciasUseCase(ast.NodeVisitor):
    def __init__(self) -> None:
        self.faltantes: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        nombre = _nombre_llamado(node.func)
        if nombre in {"BuscarAuditoriaAccesos", "ExportarAuditoriaCSV"}:
            tiene_verificador = any(keyword.arg == "verificador_integridad" for keyword in node.keywords)
            if not tiene_verificador:
                self.faltantes.append(f"{nombre} sin verificador_integridad en línea {node.lineno}")
        self.generic_visit(node)


def _nombre_llamado(nodo: ast.AST) -> str | None:
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        return nodo.attr
    return None


def test_page_auditoria_inyecta_preflight_integridad_en_buscar_y_exportar() -> None:
    contenido = RUTA_PAGE_AUDITORIA.read_text(encoding="utf-8")

    assert "BuscarAuditoriaAccesos(self._queries, verificador_integridad=self._queries)" in contenido
    assert "ExportarAuditoriaCSV(self._queries, verificador_integridad=self._queries)" in contenido


def test_usecases_auditoria_en_app_exigen_verificador_integridad_en_call_sites() -> None:
    faltantes: list[str] = []

    for ruta in RUTA_APP.rglob("*.py"):
        if ruta.name in {"buscar_auditoria_accesos.py", "exportar_auditoria_csv.py"}:
            continue
        visitor = _VisitorInstanciasUseCase()
        visitor.visit(ast.parse(ruta.read_text(encoding="utf-8")))
        if visitor.faltantes:
            faltantes.extend(f"{ruta}: {mensaje}" for mensaje in visitor.faltantes)

    assert not faltantes, "\n".join(faltantes)
