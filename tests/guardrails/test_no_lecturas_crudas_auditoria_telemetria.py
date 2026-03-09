from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

BASE_APP = Path("clinicdesk/app")
RUTAS_SELECT_PERMITIDAS = {
    Path("clinicdesk/app/queries/auditoria_accesos_queries.py"),
    Path("clinicdesk/app/queries/telemetria_eventos_queries.py"),
}
TABLAS_SENSIBLES = ("auditoria_accesos", "telemetria_eventos")

PATRON_REFERENCIA_TABLA_SENSIBLE = re.compile(
    r"\b(from|join)\b[\s\S]{0,200}?\b(auditoria_accesos|telemetria_eventos)\b"
)


@dataclass(frozen=True, slots=True)
class SqlSensibleDetectado:
    ruta: Path
    linea: int
    sql: str


class _DetectorExecuteSqlSensible(ast.NodeVisitor):
    def __init__(self, ruta: Path) -> None:
        self._ruta = ruta
        self._scopes: list[dict[str, str]] = [{}]
        self.hallazgos: list[SqlSensibleDetectado] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._enter_scope(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._enter_scope(node)

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        sql = self._resolver_sql(node.value)
        if sql is None:
            self.generic_visit(node)
            return
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._scope_actual()[target.id] = sql
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        attr = node.func.attr if isinstance(node.func, ast.Attribute) else None
        if attr in {"execute", "executemany"} and node.args:
            sql = self._resolver_sql(node.args[0])
            if sql and _es_sql_select_sensible(sql):
                self.hallazgos.append(SqlSensibleDetectado(ruta=self._ruta, linea=node.lineno, sql=sql))
        self.generic_visit(node)

    def _enter_scope(self, node: ast.AST) -> None:
        self._scopes.append({})
        self.generic_visit(node)
        self._scopes.pop()

    def _scope_actual(self) -> dict[str, str]:
        return self._scopes[-1]

    def _resolver_nombre(self, nombre: str) -> str | None:
        for scope in reversed(self._scopes):
            if nombre in scope:
                return scope[nombre]
        return None

    def _resolver_sql(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return self._resolver_nombre(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            izquierda = self._resolver_sql(node.left)
            derecha = self._resolver_sql(node.right)
            if izquierda is None or derecha is None:
                return None
            return izquierda + derecha
        if isinstance(node, ast.JoinedStr):
            piezas: list[str] = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    piezas.append(value.value)
                elif isinstance(value, ast.FormattedValue):
                    sub_sql = self._resolver_sql(value.value)
                    piezas.append(sub_sql if sub_sql is not None else "{expr}")
            return "".join(piezas)
        return None


def _es_sql_select_sensible(sql: str) -> bool:
    sql_normalizada = " ".join(sql.lower().split())
    if "select" not in sql_normalizada:
        return False
    return bool(PATRON_REFERENCIA_TABLA_SENSIBLE.search(sql_normalizada))


def _detectar_sql_sensible_en_archivo(ruta: Path) -> list[SqlSensibleDetectado]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    detector = _DetectorExecuteSqlSensible(ruta)
    detector.visit(arbol)
    return detector.hallazgos


def _detectar_sql_sensible_en_repo(base: Path = BASE_APP) -> list[SqlSensibleDetectado]:
    hallazgos: list[SqlSensibleDetectado] = []
    for ruta in sorted(base.rglob("*.py")):
        if ruta in RUTAS_SELECT_PERMITIDAS:
            continue
        hallazgos.extend(_detectar_sql_sensible_en_archivo(ruta))
    return hallazgos


def _escribir_python(tmp_path: Path, nombre: str, contenido: str) -> Path:
    ruta = tmp_path / nombre
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def _lineas(hallazgos: Iterable[SqlSensibleDetectado]) -> list[int]:
    return [h.linea for h in hallazgos]


def test_no_hay_selects_execute_fuera_de_queries_oficiales_para_tablas_sensibles() -> None:
    offenders = _detectar_sql_sensible_en_repo()
    assert not offenders, (
        "Se detectaron lecturas SQL de auditoría/telemetría fuera de queries oficiales:\n"
        + "\n".join(f"{h.ruta}:{h.linea}" for h in offenders)
    )


def test_detecta_execute_literal_select_auditoria_fuera_de_modulo_autorizado(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("SELECT id FROM auditoria_accesos")\n',
    )
    assert _lineas(_detectar_sql_sensible_en_archivo(ruta)) == [2]


def test_detecta_execute_multilinea_select_telemetria(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("""SELECT evento\nFROM telemetria_eventos\nWHERE 1=1""")\n',
    )
    assert _lineas(_detectar_sql_sensible_en_archivo(ruta)) == [2]


def test_detecta_execute_concatenacion_literal(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("SELECT id" + " FROM auditoria_accesos")\n',
    )
    assert _lineas(_detectar_sql_sensible_en_archivo(ruta)) == [2]


def test_detecta_execute_con_variable_local_simple(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    sql = "SELECT id FROM auditoria_accesos"\n    c.execute(sql)\n',
    )
    assert _lineas(_detectar_sql_sensible_en_archivo(ruta)) == [3]


def test_permite_modulos_oficiales_autorizados() -> None:
    assert not _detectar_sql_sensible_en_repo(base=Path("clinicdesk/app/queries"))


def test_no_detecta_falso_positivo_en_sql_irrelevante(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("SELECT id FROM pacientes")\n',
    )
    assert _detectar_sql_sensible_en_archivo(ruta) == []


def test_query_auditoria_aplica_saneo_de_campos_sensibles_en_lectura() -> None:
    ruta = Path("clinicdesk/app/queries/auditoria_accesos_queries.py")
    contenido = ruta.read_text(encoding="utf-8")

    assert 'sanear_valor_pii(row["usuario"], clave="usuario")' in contenido
    assert 'sanear_valor_pii(row["entidad_id"], clave="entidad_id")' in contenido


def test_query_telemetria_no_expone_columnas_sensibles_en_resumen() -> None:
    ruta = Path("clinicdesk/app/queries/telemetria_eventos_queries.py")
    contenido = ruta.read_text(encoding="utf-8").lower()

    assert "from telemetria_eventos" in contenido
    for columna_sensible in ("usuario", "contexto", "entidad_id", "payload", "detalle", "extra"):
        assert columna_sensible not in contenido.split("from telemetria_eventos", maxsplit=1)[0]
