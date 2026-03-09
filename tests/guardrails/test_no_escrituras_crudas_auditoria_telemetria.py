from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

BASE_APP = Path("clinicdesk/app")
RUTAS_ESCRITURA_PERMITIDAS = {
    Path("clinicdesk/app/infrastructure/sqlite/repos_auditoria_accesos.py"),
    Path("clinicdesk/app/infrastructure/sqlite/repos_telemetria_eventos.py"),
}
TABLAS_SENSIBLES = ("auditoria_accesos", "telemetria_eventos")
PATRON_SQL_ESCRITURA_SENSIBLE = re.compile(
    r"\b(?:insert(?:\s+or\s+replace)?\s+into|update|delete\s+from|replace\s+into)\s+"
    r"(?:\w+\.)?(auditoria_accesos|telemetria_eventos)\b"
)
PATRON_UPSERT_UPDATE_SENSIBLE = re.compile(
    r"\binsert\b[\s\S]{0,400}?\binto\s+(?:\w+\.)?"
    r"(?:auditoria_accesos|telemetria_eventos)\b[\s\S]{0,400}?\bon\s+conflict\b[\s\S]{0,200}?\bdo\s+update\b"
)
CONTRATOS_SANEAMIENTO_POR_MODULO: dict[Path, tuple[str, ...]] = {
    Path("clinicdesk/app/infrastructure/sqlite/repos_auditoria_accesos.py"): (
        "sanear_evento_auditoria_para_persistencia",
    ),
    Path("clinicdesk/app/infrastructure/sqlite/repos_telemetria_eventos.py"): (
        "sanear_evento_auditoria_para_persistencia",
        "sanear_contexto_telemetria_para_persistencia",
    ),
}

CONTRATOS_INTEGRIDAD_POR_MODULO: dict[Path, tuple[str, ...]] = {
    Path("clinicdesk/app/infrastructure/sqlite/repos_auditoria_accesos.py"): ("siguiente_hash_acceso",),
    Path("clinicdesk/app/infrastructure/sqlite/repos_auditoria_eventos.py"): ("siguiente_hash_evento",),
    Path("clinicdesk/app/application/usecases/buscar_auditoria_accesos.py"): ("exigir_integridad_auditoria",),
    Path("clinicdesk/app/application/usecases/exportar_auditoria_csv.py"): ("exigir_integridad_auditoria",),
    Path("scripts/verify_audit_chain.py"): ("verificar_cadena",),
    Path("scripts/verify_telemetry_chain.py"): ("verificar_cadena_telemetria",),
}


@dataclass(frozen=True, slots=True)
class SqlEscrituraSensibleDetectada:
    ruta: Path
    linea: int
    sql: str


class _DetectorExecuteSqlEscrituraSensible(ast.NodeVisitor):
    def __init__(self, ruta: Path) -> None:
        self._ruta = ruta
        self._scopes: list[dict[str, str]] = [{}]
        self.hallazgos: list[SqlEscrituraSensibleDetectada] = []

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
            if sql and _es_sql_escritura_sensible(sql):
                self.hallazgos.append(SqlEscrituraSensibleDetectada(ruta=self._ruta, linea=node.lineno, sql=sql))
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


class _DetectorLlamadasSaneo(ast.NodeVisitor):
    def __init__(self) -> None:
        self.llamadas: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name):
            self.llamadas.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.llamadas.add(node.func.attr)
        self.generic_visit(node)


def _es_sql_escritura_sensible(sql: str) -> bool:
    sql_normalizada = " ".join(sql.lower().split())
    if not any(tabla in sql_normalizada for tabla in TABLAS_SENSIBLES):
        return False
    return bool(
        PATRON_SQL_ESCRITURA_SENSIBLE.search(sql_normalizada) or PATRON_UPSERT_UPDATE_SENSIBLE.search(sql_normalizada)
    )


def _detectar_escrituras_sensibles_en_archivo(ruta: Path) -> list[SqlEscrituraSensibleDetectada]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    detector = _DetectorExecuteSqlEscrituraSensible(ruta)
    detector.visit(arbol)
    return detector.hallazgos


def _detectar_escrituras_sensibles_en_repo(base: Path = BASE_APP) -> list[SqlEscrituraSensibleDetectada]:
    hallazgos: list[SqlEscrituraSensibleDetectada] = []
    for ruta in sorted(base.rglob("*.py")):
        if ruta in RUTAS_ESCRITURA_PERMITIDAS:
            continue
        hallazgos.extend(_detectar_escrituras_sensibles_en_archivo(ruta))
    return hallazgos


def _escribir_python(tmp_path: Path, nombre: str, contenido: str) -> Path:
    ruta = tmp_path / nombre
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def _lineas(hallazgos: Iterable[SqlEscrituraSensibleDetectada]) -> list[int]:
    return [h.linea for h in hallazgos]


def _llamadas_de_saneo_en_modulo(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    detector = _DetectorLlamadasSaneo()
    detector.visit(arbol)
    return detector.llamadas


def _validar_contrato_saneo_modulo_oficial(ruta: Path, requeridas: tuple[str, ...]) -> list[str]:
    llamadas = _llamadas_de_saneo_en_modulo(ruta)
    return [funcion for funcion in requeridas if funcion not in llamadas]


def test_no_hay_escrituras_execute_fuera_del_boundary_oficial_para_tablas_sensibles() -> None:
    offenders = _detectar_escrituras_sensibles_en_repo()
    assert not offenders, (
        "Se detectaron escrituras SQL de auditoría/telemetría fuera del boundary oficial:\n"
        + "\n".join(f"{h.ruta}:{h.linea}" for h in offenders)
    )


def test_detecta_insert_auditoria_fuera_de_allowlist(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("INSERT INTO auditoria_accesos(usuario) VALUES (?)", ("u",))\n',
    )
    assert _lineas(_detectar_escrituras_sensibles_en_archivo(ruta)) == [2]


def test_detecta_update_telemetria_fuera_de_allowlist(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("UPDATE telemetria_eventos SET usuario = ?", ("u",))\n',
    )
    assert _lineas(_detectar_escrituras_sensibles_en_archivo(ruta)) == [2]


def test_detecta_delete_auditoria_fuera_de_allowlist(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("DELETE FROM auditoria_accesos WHERE id = ?", (1,))\n',
    )
    assert _lineas(_detectar_escrituras_sensibles_en_archivo(ruta)) == [2]


def test_detecta_delete_telemetria_fuera_de_allowlist(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    sql = "DELETE FROM telemetria_eventos WHERE id = ?"\n    c.executemany(sql, [(1,)])\n',
    )
    assert _lineas(_detectar_escrituras_sensibles_en_archivo(ruta)) == [3]


def test_detecta_sql_sensible_multilinea(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("""INSERT INTO telemetria_eventos(evento)\nVALUES (?)""", ("open",))\n',
    )
    assert _lineas(_detectar_escrituras_sensibles_en_archivo(ruta)) == [2]


def test_detecta_sql_sensible_por_concatenacion(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("REPLACE INTO " + "auditoria_accesos(usuario) VALUES (?)", ("u",))\n',
    )
    assert _lineas(_detectar_escrituras_sensibles_en_archivo(ruta)) == [2]


def test_detecta_sql_sensible_via_variable_local(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    sql = "INSERT OR REPLACE INTO telemetria_eventos(evento) VALUES (?)"\n    c.executemany(sql, [("a",)])\n',
    )
    assert _lineas(_detectar_escrituras_sensibles_en_archivo(ruta)) == [3]


def test_detecta_sql_sensible_via_upsert_on_conflict(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("INSERT INTO auditoria_accesos(usuario) VALUES (?) ON CONFLICT(id) DO UPDATE SET usuario=excluded.usuario", ("u",))\n',
    )
    assert _lineas(_detectar_escrituras_sensibles_en_archivo(ruta)) == [2]


def test_no_detecta_falso_positivo_en_select_sensible_de_guardrail_de_lectura(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "modulo.py",
        'def x(c):\n    c.execute("SELECT id FROM auditoria_accesos")\n',
    )
    assert _detectar_escrituras_sensibles_en_archivo(ruta) == []


def test_no_da_falso_positivo_en_modulos_oficiales_allowlist() -> None:
    assert not _detectar_escrituras_sensibles_en_repo(base=Path("clinicdesk/app/infrastructure/sqlite"))


def test_modulos_oficiales_usan_helper_obligatorio_de_saneo() -> None:
    faltantes: list[str] = []
    for ruta, funciones_requeridas in CONTRATOS_SANEAMIENTO_POR_MODULO.items():
        faltan = _validar_contrato_saneo_modulo_oficial(ruta, funciones_requeridas)
        if faltan:
            faltantes.append(f"{ruta}: faltan {', '.join(faltan)}")

    assert not faltantes, "Contrato de saneo roto en módulos oficiales:\n" + "\n".join(faltantes)


def test_falla_contrato_si_desaparece_llamada_al_helper_en_modulo_oficial(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "repos_auditoria_accesos.py",
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class RepositorioAuditoriaAccesoSqlite:\n"
        "    def registrar(self, evento):\n"
        "        self.connection.execute('INSERT INTO auditoria_accesos(usuario) VALUES (?)', ('u',))\n",
    )
    assert _validar_contrato_saneo_modulo_oficial(ruta, ("sanear_evento_auditoria_para_persistencia",)) == [
        "sanear_evento_auditoria_para_persistencia"
    ]


def test_modulos_oficiales_usan_helper_obligatorio_de_integridad() -> None:
    faltantes: list[str] = []
    for ruta, funciones_requeridas in CONTRATOS_INTEGRIDAD_POR_MODULO.items():
        faltan = _validar_contrato_saneo_modulo_oficial(ruta, funciones_requeridas)
        if faltan:
            faltantes.append(f"{ruta}: faltan {', '.join(faltan)}")

    assert not faltantes, "Contrato de integridad roto en módulos oficiales:\n" + "\n".join(faltantes)


def test_falla_contrato_si_desaparece_llamada_de_integridad_en_modulo_oficial(tmp_path: Path) -> None:
    ruta = _escribir_python(
        tmp_path,
        "repos_auditoria_accesos.py",
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class RepositorioAuditoriaAccesoSqlite:\n"
        "    def registrar(self, evento):\n"
        "        self.connection.execute('INSERT INTO auditoria_accesos(usuario) VALUES (?)', ('u',))\n",
    )
    assert _validar_contrato_saneo_modulo_oficial(ruta, ("siguiente_hash_acceso",)) == ["siguiente_hash_acceso"]
