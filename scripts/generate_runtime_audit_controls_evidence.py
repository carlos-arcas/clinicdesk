from __future__ import annotations

import argparse
import sqlite3
import tempfile
from pathlib import Path

from clinicdesk.app.application.auditoria.audit_service import AuditEvent
from clinicdesk.app.application.auditoria_acceso import (
    AccionAuditoriaAcceso,
    EntidadAuditoriaAcceso,
    EventoAuditoriaAcceso,
)
from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
from clinicdesk.app.bootstrap import schema_path
from clinicdesk.app.infrastructure.sqlite import db as sqlite_db
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_accesos import RepositorioAuditoriaAccesoSqlite
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_eventos import RepositorioAuditoriaEventosSqlite
from clinicdesk.app.infrastructure.sqlite.repos_telemetria_eventos import RepositorioTelemetriaEventosSqlite
from scripts import verify_audit_runtime_controls

RUTA_SALIDA_DEFAULT = Path("docs/runtime_audit_controls.json")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera evidencia runtime de controles de auditoría/telemetría")
    parser.add_argument("--out", default=RUTA_SALIDA_DEFAULT.as_posix(), help="Ruta del JSON de evidencia")
    return parser.parse_args(argv)


def poblar_db_evidencia(con: sqlite3.Connection) -> None:
    repo_accesos = RepositorioAuditoriaAccesoSqlite(con)
    repo_eventos = RepositorioAuditoriaEventosSqlite(con)
    repo_telemetria = RepositorioTelemetriaEventosSqlite(con)

    repo_accesos.registrar(
        EventoAuditoriaAcceso(
            timestamp_utc="2026-01-08T10:00:00+00:00",
            usuario="ci_runtime",
            modo_demo=False,
            accion=AccionAuditoriaAcceso.VER_DETALLE_CITA,
            entidad_tipo=EntidadAuditoriaAcceso.CITA,
            entidad_id="100",
        )
    )
    repo_accesos.registrar(
        EventoAuditoriaAcceso(
            timestamp_utc="2026-01-08T10:01:00+00:00",
            usuario="ci_runtime",
            modo_demo=False,
            accion=AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE,
            entidad_tipo=EntidadAuditoriaAcceso.PACIENTE,
            entidad_id="200",
        )
    )

    repo_eventos.append(
        AuditEvent(
            action="runtime_controls_probe",
            outcome="ok",
            actor_username="ci_runtime",
            actor_role="system",
            correlation_id="runtime-corr-1",
            metadata={"origen": "ci", "tipo": "evidencia"},
            timestamp_utc="2026-01-08T10:00:00+00:00",
        )
    )
    repo_eventos.append(
        AuditEvent(
            action="runtime_controls_probe",
            outcome="ok",
            actor_username="ci_runtime",
            actor_role="system",
            correlation_id="runtime-corr-2",
            metadata={"origen": "ci", "tipo": "evidencia"},
            timestamp_utc="2026-01-08T10:01:00+00:00",
        )
    )

    repo_telemetria.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-08T10:00:00+00:00",
            usuario="ci_runtime",
            modo_demo=False,
            evento="runtime_controls_check",
            contexto='{"page":"quality_gate","source":"ci"}',
            entidad_tipo="sistema",
            entidad_id="100",
        )
    )
    repo_telemetria.registrar(
        EventoTelemetriaDTO(
            timestamp_utc="2026-01-08T10:01:00+00:00",
            usuario="ci_runtime",
            modo_demo=False,
            evento="runtime_controls_check",
            contexto='{"page":"quality_gate","source":"ci"}',
            entidad_tipo="sistema",
            entidad_id="101",
        )
    )


def generar_evidencia_runtime(*, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="runtime-audit-evidence-") as tempdir:
        db_path = Path(tempdir) / "runtime_audit_evidence.sqlite"
        con = sqlite_db.bootstrap(db_path, schema_path(), apply=True)
        try:
            poblar_db_evidencia(con)
        finally:
            con.close()

        return verify_audit_runtime_controls.main(["--db-path", db_path.as_posix(), "--out", out_path.as_posix()])


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return generar_evidencia_runtime(out_path=Path(args.out))


if __name__ == "__main__":
    raise SystemExit(main())
