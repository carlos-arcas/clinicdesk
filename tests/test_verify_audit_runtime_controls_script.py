from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from clinicdesk.app.application.auditoria.audit_service import AuditEvent
from clinicdesk.app.application.auditoria_acceso import (
    AccionAuditoriaAcceso,
    EntidadAuditoriaAcceso,
    EventoAuditoriaAcceso,
)
from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_accesos import RepositorioAuditoriaAccesoSqlite
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_eventos import RepositorioAuditoriaEventosSqlite
from clinicdesk.app.infrastructure.sqlite.repos_telemetria_eventos import RepositorioTelemetriaEventosSqlite
from scripts import verify_audit_runtime_controls

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "clinicdesk" / "app" / "infrastructure" / "sqlite" / "schema.sql"


def _crear_db_sana(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path.as_posix())
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    RepositorioAuditoriaAccesoSqlite(con).registrar(
        EventoAuditoriaAcceso(
            timestamp_utc="2026-01-08T10:00:00+00:00",
            usuario="tester",
            modo_demo=False,
            accion=AccionAuditoriaAcceso.VER_DETALLE_CITA,
            entidad_tipo=EntidadAuditoriaAcceso.CITA,
            entidad_id="99",
        )
    )
    RepositorioAuditoriaEventosSqlite(con).append(
        AuditEvent(
            action="cita_open",
            outcome="ok",
            actor_username="tester",
            actor_role="admin",
            correlation_id="corr-1",
            metadata={"db_path_hint": "test"},
            timestamp_utc="2026-01-08T10:00:00+00:00",
        )
    )
    RepositorioTelemetriaEventosSqlite(con).registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-08T10:00:00+00:00",
            usuario="tester",
            modo_demo=False,
            evento="gestion_abrir_cita",
            contexto='{"page":"gestion"}',
            entidad_tipo="cita",
            entidad_id="99",
        )
    )
    return con


def _json_stdout(capsys) -> dict[str, object]:
    return json.loads(capsys.readouterr().out)


def test_db_sana_retorna_ok_y_json_estable(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "runtime-ok.sqlite"
    _crear_db_sana(db_path)

    exit_code = verify_audit_runtime_controls.main(["--db-path", db_path.as_posix()])

    assert exit_code == 0
    reporte = _json_stdout(capsys)
    assert reporte["status"] == "ok"
    assert reporte["db_path"] == db_path.as_posix()
    assert "generated_at" in reporte
    controles = {control["name"]: control for control in reporte["controls"]}
    assert controles["auditoria.chain"]["status"] == "ok"
    assert controles["telemetria.chain"]["status"] == "ok"
    assert controles["auditoria.append_only.auditoria_accesos"]["status"] == "ok"
    assert controles["telemetria.append_only.telemetria_eventos"]["status"] == "ok"


def test_cadena_auditoria_rota_falla(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "runtime-audit-fail.sqlite"
    con = _crear_db_sana(db_path)
    con.execute("DROP TRIGGER IF EXISTS trg_auditoria_accesos_no_update")
    con.execute("UPDATE auditoria_accesos SET usuario = 'manipulado' WHERE id = 1")
    con.commit()

    exit_code = verify_audit_runtime_controls.main(["--db-path", db_path.as_posix()])

    assert exit_code == 1
    reporte = _json_stdout(capsys)
    assert reporte["status"] == "failed"
    controles = {control["name"]: control for control in reporte["controls"]}
    assert controles["auditoria.chain"]["status"] == "failed"


def test_cadena_telemetria_rota_falla(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "runtime-telemetry-fail.sqlite"
    con = _crear_db_sana(db_path)
    con.execute("DROP TRIGGER IF EXISTS trg_telemetria_eventos_no_update")
    con.execute("UPDATE telemetria_eventos SET evento = 'manipulado' WHERE id = 1")
    con.commit()

    exit_code = verify_audit_runtime_controls.main(["--db-path", db_path.as_posix()])

    assert exit_code == 1
    reporte = _json_stdout(capsys)
    controles = {control["name"]: control for control in reporte["controls"]}
    assert controles["telemetria.chain"]["status"] == "failed"


def test_append_only_ausente_en_tabla_sensible_falla(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "runtime-append-fail.sqlite"
    con = _crear_db_sana(db_path)
    con.execute("DROP TRIGGER IF EXISTS trg_auditoria_accesos_no_update")
    con.commit()

    exit_code = verify_audit_runtime_controls.main(["--db-path", db_path.as_posix()])

    assert exit_code == 1
    reporte = _json_stdout(capsys)
    controles = {control["name"]: control for control in reporte["controls"]}
    assert controles["auditoria.append_only.auditoria_accesos"]["status"] == "failed"


def test_json_contiene_claves_estables_y_out(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "runtime-json.sqlite"
    out_path = tmp_path / "reporte.json"
    _crear_db_sana(db_path)

    exit_code = verify_audit_runtime_controls.main(["--db-path", db_path.as_posix(), "--out", out_path.as_posix()])

    assert exit_code == 0
    reporte_stdout = _json_stdout(capsys)
    reporte_archivo = json.loads(out_path.read_text(encoding="utf-8"))
    assert reporte_stdout == reporte_archivo
    assert set(reporte_stdout.keys()) == {"controls", "db_path", "generated_at", "status"}


def test_script_reutiliza_verificadores_oficiales(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "runtime-contract.sqlite"
    _crear_db_sana(db_path)
    llamadas: list[str] = []

    original_auditoria = verify_audit_runtime_controls.verificar_cadena
    original_telemetria = verify_audit_runtime_controls.verificar_cadena_telemetria

    def _spy_auditoria(con):
        llamadas.append("auditoria")
        return original_auditoria(con)

    def _spy_telemetria(con):
        llamadas.append("telemetria")
        return original_telemetria(con)

    monkeypatch.setattr(verify_audit_runtime_controls, "verificar_cadena", _spy_auditoria)
    monkeypatch.setattr(verify_audit_runtime_controls, "verificar_cadena_telemetria", _spy_telemetria)

    assert verify_audit_runtime_controls.main(["--db-path", db_path.as_posix()]) == 0
    assert llamadas == ["auditoria", "telemetria"]
