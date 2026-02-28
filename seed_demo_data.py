from __future__ import annotations

import argparse
import sqlite3
import sys
import uuid
from datetime import date
from pathlib import Path

from scripts.ml_cli import run_cli
from clinicdesk.app.bootstrap_logging import configure_logging, get_logger, log_soft_exception, set_run_context
from clinicdesk.app.crash_handler import install_global_exception_hook

_DEFAULT_SQLITE_PATH = "./data/demo.db"
_DEFAULT_FROM_DATE = "2025-01-01"
_DEFAULT_TO_DATE = "2026-02-28"
_LOGGER = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lanzador de siembra de datos demo (sin subprocess).")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--doctors", type=int, default=25)
    parser.add_argument("--patients", type=int, default=500)
    parser.add_argument("--appointments", type=int, default=5000)
    parser.add_argument("--from", dest="from_date", type=str, default=_DEFAULT_FROM_DATE)
    parser.add_argument("--to", dest="to_date", type=str, default=_DEFAULT_TO_DATE)
    parser.add_argument("--incidence-rate", type=float, default=0.15)
    parser.add_argument("--sqlite-path", type=str, default=_DEFAULT_SQLITE_PATH)
    parser.add_argument("--reset", dest="reset", action="store_true", default=True)
    parser.add_argument("--no-reset", dest="reset", action="store_false")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging("clinicdesk-seed-demo", Path("./logs"), level="INFO", json=True)
    set_run_context(uuid.uuid4().hex[:8])
    install_global_exception_hook(_LOGGER)
    args = build_parser().parse_args(argv)
    try:
        sqlite_path = _validate_args(args)
        if args.reset:
            _reset_demo_db_if_allowed(sqlite_path)

        cli_args = [
            "seed-demo",
            "--seed",
            str(args.seed),
            "--doctors",
            str(args.doctors),
            "--patients",
            str(args.patients),
            "--appointments",
            str(args.appointments),
            "--from",
            args.from_date,
            "--to",
            args.to_date,
            "--incidence-rate",
            str(args.incidence_rate),
            "--sqlite-path",
            str(sqlite_path),
        ]
        rc = run_cli(cli_args)
        if rc != 0:
            return rc

        counts = _fetch_counts(sqlite_path)
        _print_summary(counts, sqlite_path, args.from_date, args.to_date)
        return 0
    except ValueError as exc:
        log_soft_exception(_LOGGER, exc, {"command": "seed_demo_data"})
        return 2


def _validate_args(args: argparse.Namespace) -> Path:
    if args.seed < 0:
        raise ValueError("--seed debe ser >= 0")
    if args.doctors <= 0:
        raise ValueError("--doctors debe ser > 0")
    if args.patients <= 0:
        raise ValueError("--patients debe ser > 0")
    if args.appointments <= 0:
        raise ValueError("--appointments debe ser > 0")
    if not (0.0 <= args.incidence_rate <= 1.0):
        raise ValueError("--incidence-rate debe estar entre 0.0 y 1.0")

    from_date = date.fromisoformat(args.from_date)
    to_date = date.fromisoformat(args.to_date)
    if to_date < from_date:
        raise ValueError("Rango inválido: --to no puede ser menor que --from")

    sqlite_path = Path(args.sqlite_path).expanduser().resolve()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite_path


def _reset_demo_db_if_allowed(sqlite_path: Path) -> None:
    if not sqlite_path.exists():
        return
    if not _is_safe_demo_db_path(sqlite_path):
        raise ValueError(
            "--reset solo permite borrar bases demo bajo ./data/*.db para evitar borrados accidentales. "
            f"Ruta recibida: {sqlite_path}"
        )
    sqlite_path.unlink()
    _LOGGER.info("[reset] base demo eliminada: %s", sqlite_path)


def _is_safe_demo_db_path(sqlite_path: Path) -> bool:
    repo_root = Path(__file__).resolve().parent
    data_dir = (repo_root / "data").resolve()
    return sqlite_path.suffix == ".db" and data_dir in sqlite_path.parents


def _fetch_counts(sqlite_path: Path) -> dict[str, int]:
    with sqlite3.connect(sqlite_path.as_posix()) as conn:
        return {
            "medicos": _count_table(conn, "medicos"),
            "pacientes": _count_table(conn, "pacientes"),
            "personal": _count_table(conn, "personal"),
            "citas": _count_table(conn, "citas"),
            "incidencias": _count_table(conn, "incidencias"),
        }


def _count_table(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0]) if row else 0


def _print_summary(counts: dict[str, int], sqlite_path: Path, from_date: str, to_date: str) -> None:
    _LOGGER.info("=== RESUMEN DEMO ===")
    _LOGGER.info(
        "Conteos creados: "
        f"medicos={counts['medicos']} pacientes={counts['pacientes']} "
        f"personal={counts['personal']} citas={counts['citas']} incidencias={counts['incidencias']}"
    )
    _LOGGER.info("Base de datos: %s", sqlite_path)
    _LOGGER.info("Siguientes pasos sugeridos:")
    _LOGGER.info("  PYTHONPATH=. python scripts/ml_cli.py build-features --from %s --to %s --store-path ./data/feature_store", from_date, to_date)
    _LOGGER.info("  PYTHONPATH=. python scripts/ml_cli.py train --dataset-version <version> --model-version m_demo --feature-store-path ./data/feature_store --model-store-path ./data/model_store")
    _LOGGER.info("  PYTHONPATH=. python scripts/ml_cli.py export features --dataset-version <version> --output ./exports --feature-store-path ./data/feature_store")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
