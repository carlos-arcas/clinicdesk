from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from clinicdesk.app.bootstrap import resolve_db_path
from clinicdesk.app.infrastructure.sqlite.auditoria_integridad import verificar_cadena, verificar_cadena_telemetria
from clinicdesk.app.infrastructure.sqlite.runtime_audit_controls import verificar_append_only_tabla

EXIT_OK = 0
EXIT_CONTROLES_FAILED = 1
EXIT_DB_UNAVAILABLE = 2


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica controles runtime de auditoría y telemetría")
    parser.add_argument("--db-path", help="Ruta a la DB sqlite. Si no se indica, usa resolución oficial.")
    parser.add_argument("--out", help="Ruta opcional para guardar el JSON de salida.")
    return parser.parse_args(argv)


def _control(name: str, status: str, details: str, *, critical: bool) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "details": details,
        "critical": critical,
    }


def _resolver_db_path(db_path_arg: str | None) -> Path:
    return resolve_db_path(db_path_arg, emit_log=False)


def build_report(db_path: Path) -> dict[str, Any]:
    controles: list[dict[str, Any]] = []

    with sqlite3.connect(db_path.as_posix()) as con:
        con.row_factory = sqlite3.Row

        estado_auditoria = verificar_cadena(con)
        if estado_auditoria.ok:
            controles.append(_control("auditoria.chain", "ok", "cadena integra", critical=True))
        else:
            detalle = f"tabla={estado_auditoria.tabla}, primer_fallo_id={estado_auditoria.primer_fallo_id}"
            controles.append(_control("auditoria.chain", "failed", detalle, critical=True))

        append_auditoria_accesos = verificar_append_only_tabla(con, "auditoria_accesos")
        status_auditoria_accesos = "ok" if append_auditoria_accesos.ok else "failed"
        controles.append(
            _control(
                "auditoria.append_only.auditoria_accesos",
                status_auditoria_accesos,
                append_auditoria_accesos.detalle,
                critical=True,
            )
        )

        append_auditoria_eventos = verificar_append_only_tabla(con, "auditoria_eventos")
        status_eventos = "ok" if append_auditoria_eventos.ok else "failed"
        controles.append(
            _control(
                "auditoria.append_only.auditoria_eventos",
                status_eventos,
                append_auditoria_eventos.detalle,
                critical=True,
            )
        )

        estado_telemetria = verificar_cadena_telemetria(con)
        if estado_telemetria.ok:
            controles.append(_control("telemetria.chain", "ok", "cadena integra", critical=True))
        else:
            detalle = f"tabla={estado_telemetria.tabla}, primer_fallo_id={estado_telemetria.primer_fallo_id}"
            controles.append(_control("telemetria.chain", "failed", detalle, critical=True))

        append_telemetria = verificar_append_only_tabla(con, "telemetria_eventos")
        status_telemetria = "ok" if append_telemetria.ok else "failed"
        controles.append(
            _control(
                "telemetria.append_only.telemetria_eventos",
                status_telemetria,
                append_telemetria.detalle,
                critical=True,
            )
        )

    status_global = "ok"
    for control in controles:
        if control["critical"] and control["status"] != "ok":
            status_global = "failed"
            break

    return {
        "status": status_global,
        "db_path": db_path.as_posix(),
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "controls": controles,
    }


def build_error_report(db_path: Path, *, error_code: str, message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "db_path": db_path.as_posix(),
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "controls": [],
        "error_code": error_code,
        "message": message,
    }


def _emit_output(report: dict[str, Any], out_path: str | None) -> None:
    output = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if out_path:
        Path(out_path).write_text(output + "\n", encoding="utf-8")
    sys.stdout.write(output + "\n")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    db_path = _resolver_db_path(args.db_path)
    try:
        report = build_report(db_path)
    except sqlite3.OperationalError as exc:
        report = build_error_report(
            db_path,
            error_code="db_unavailable",
            message=(
                "No se pudo abrir la DB SQLite. Verifica que la ruta exista y tenga permisos de lectura/escritura. "
                f"Detalle SQLite: {exc}"
            ),
        )
        _emit_output(report, args.out)
        return EXIT_DB_UNAVAILABLE

    _emit_output(report, args.out)
    return EXIT_OK if report["status"] == "ok" else EXIT_CONTROLES_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
