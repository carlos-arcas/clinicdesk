from __future__ import annotations

import ast
import json
import sqlite3
from pathlib import Path

from scripts import generate_runtime_audit_controls_evidence as modulo
from scripts import verify_audit_runtime_controls


def test_generar_evidencia_crea_json_y_db_no_vacia(tmp_path: Path, monkeypatch) -> None:
    out_path = tmp_path / "runtime_audit_controls.json"
    conteos: dict[str, int] = {}

    original_main = verify_audit_runtime_controls.main

    def _capturar_db(argv: list[str] | None = None) -> int:
        assert argv is not None
        db_path = Path(argv[argv.index("--db-path") + 1])
        with sqlite3.connect(db_path.as_posix()) as con:
            conteos["auditoria_accesos"] = con.execute("SELECT COUNT(*) FROM auditoria_accesos").fetchone()[0]
            conteos["telemetria_eventos"] = con.execute("SELECT COUNT(*) FROM telemetria_eventos").fetchone()[0]
        return original_main(argv)

    monkeypatch.setattr(modulo.verify_audit_runtime_controls, "main", _capturar_db)

    exit_code = modulo.generar_evidencia_runtime(out_path=out_path)

    assert exit_code == 0
    assert out_path.exists()
    reporte = json.loads(out_path.read_text(encoding="utf-8"))
    controles = {control["name"]: control for control in reporte["controls"]}
    assert controles["auditoria.chain"]["status"] == "ok"
    assert controles["telemetria.chain"]["status"] == "ok"
    assert controles["auditoria.append_only.auditoria_accesos"]["status"] == "ok"
    assert controles["auditoria.append_only.auditoria_eventos"]["status"] == "ok"
    assert controles["telemetria.append_only.telemetria_eventos"]["status"] == "ok"

    assert conteos["auditoria_accesos"] >= 2
    assert conteos["telemetria_eventos"] >= 2


def test_generacion_reutiliza_verificador_oficial(tmp_path: Path, monkeypatch) -> None:
    out_path = tmp_path / "runtime_audit_controls.json"
    llamadas: list[list[str]] = []

    def _fake_main(argv: list[str] | None = None) -> int:
        assert argv is not None
        llamadas.append(argv)
        out = Path(argv[argv.index("--out") + 1])
        out.write_text('{"status":"ok","controls":[]}', encoding="utf-8")
        return 0

    monkeypatch.setattr(modulo.verify_audit_runtime_controls, "main", _fake_main)

    assert modulo.generar_evidencia_runtime(out_path=out_path) == 0
    assert len(llamadas) == 1
    assert "--db-path" in llamadas[0]
    assert "--out" in llamadas[0]


def test_si_se_rompe_cadena_el_reporte_falla(tmp_path: Path) -> None:
    db_path = tmp_path / "broken.sqlite"
    con = modulo.sqlite_db.bootstrap(db_path, modulo.schema_path(), apply=True)
    try:
        modulo.poblar_db_evidencia(con)
        con.execute("DROP TRIGGER IF EXISTS trg_telemetria_eventos_no_update")
        con.execute("UPDATE telemetria_eventos SET evento = 'manipulado' WHERE id = 1")
        con.commit()
    finally:
        con.close()

    out_path = tmp_path / "broken_report.json"
    exit_code = verify_audit_runtime_controls.main(["--db-path", db_path.as_posix(), "--out", out_path.as_posix()])

    assert exit_code == 1
    reporte = json.loads(out_path.read_text(encoding="utf-8"))
    controles = {control["name"]: control for control in reporte["controls"]}
    assert controles["telemetria.chain"]["status"] == "failed"


def test_guardrail_workflow_publica_runtime_audit_controls_artifact() -> None:
    workflow = Path(".github/workflows/quality_gate.yml").read_text(encoding="utf-8")
    assert "python -m scripts.generate_runtime_audit_controls_evidence" in workflow
    assert "docs/runtime_audit_controls.json" in workflow


def test_guardrail_estructura_generador_runtime() -> None:
    ruta = Path("scripts/generate_runtime_audit_controls_evidence.py")
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    funciones = {nodo.name: nodo for nodo in arbol.body if isinstance(nodo, ast.FunctionDef)}

    helpers_esperados = {
        "_poblar_auditoria_accesos",
        "_poblar_auditoria_eventos",
        "_poblar_telemetria",
    }
    assert helpers_esperados.issubset(funciones)

    funcion_orquestadora = funciones["poblar_db_evidencia"]
    assert (funcion_orquestadora.end_lineno or 0) - funcion_orquestadora.lineno + 1 <= 40
