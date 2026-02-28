from __future__ import annotations

import argparse
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from clinicdesk.app.infrastructure.sqlite import db
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection

LOGGER = logging.getLogger("scripts.crypto_migrate_patients")
_PROTECTED_FIELDS = ("documento", "telefono", "email", "direccion")
_REQUIRED_CONFIRMATION = "WIPE-LEGACY"


@dataclass(frozen=True)
class MigrationStats:
    scanned: int = 0
    backfilled: int = 0
    wiped: int = 0


@dataclass(frozen=True)
class MigrationOptions:
    db_path: Path
    schema_path: Path
    wipe_legacy: bool
    confirm_wipe: str


def parse_args() -> MigrationOptions:
    parser = argparse.ArgumentParser(description="Backfill seguro de cifrado por campo en pacientes")
    parser.add_argument("--db-path", required=True, type=Path)
    parser.add_argument(
        "--schema-path",
        default=Path("clinicdesk/app/infrastructure/sqlite/schema.sql"),
        type=Path,
    )
    parser.add_argument("--wipe-legacy", action="store_true")
    parser.add_argument("--confirm-wipe", default="", type=str)
    args = parser.parse_args()
    return MigrationOptions(
        db_path=args.db_path,
        schema_path=args.schema_path,
        wipe_legacy=bool(args.wipe_legacy),
        confirm_wipe=str(args.confirm_wipe),
    )


def run(options: MigrationOptions) -> MigrationStats:
    _configure_logging()
    _validate_options(options)
    con = db.bootstrap(options.db_path, options.schema_path, apply=True)
    try:
        return _migrate(con, options.wipe_legacy)
    finally:
        con.close()


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def _validate_options(options: MigrationOptions) -> None:
    if not options.wipe_legacy:
        return
    if options.confirm_wipe != _REQUIRED_CONFIRMATION:
        raise ValueError("--wipe-legacy requiere --confirm-wipe WIPE-LEGACY")
    _ensure_data_path(options.db_path)


def _ensure_data_path(db_path: Path) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    data_root = (repo_root / "data").resolve()
    resolved_db = db_path.resolve()
    if data_root not in resolved_db.parents and resolved_db != data_root:
        raise ValueError("--wipe-legacy solo permitido para bases dentro de ./data")


def _migrate(con: sqlite3.Connection, wipe_legacy: bool) -> MigrationStats:
    protection = PacientesFieldProtection(con)
    if not protection.has_columns:
        raise RuntimeError("La tabla pacientes no tiene columnas *_enc/_hash")
    if not protection.enabled:
        raise RuntimeError("CLINICDESK_FIELD_CRYPTO=1 y CLINICDESK_CRYPTO_KEY son obligatorios")

    rows = con.execute("SELECT * FROM pacientes").fetchall()
    nullable_columns = _nullable_columns(con)
    stats = MigrationStats(scanned=len(rows))
    for row in rows:
        stats = _migrate_row(
            con,
            row=row,
            protection=protection,
            wipe_legacy=wipe_legacy,
            nullable_columns=nullable_columns,
            stats=stats,
        )
    con.commit()
    LOGGER.info("crypto_migration.completed", extra={"scanned": stats.scanned, "backfilled": stats.backfilled, "wiped": stats.wiped})
    return stats


def _migrate_row(
    con: sqlite3.Connection,
    *,
    row: sqlite3.Row,
    protection: PacientesFieldProtection,
    wipe_legacy: bool,
    nullable_columns: set[str],
    stats: MigrationStats,
) -> MigrationStats:
    updates = _build_backfill_updates(row, protection, con)
    if not updates and not wipe_legacy:
        return stats
    if updates:
        _execute_update(con, row_id=int(row["id"]), updates=updates)
        stats = MigrationStats(scanned=stats.scanned, backfilled=stats.backfilled + 1, wiped=stats.wiped)
    if not wipe_legacy:
        return stats
    wipe_updates = _build_wipe_updates(row=row, updates=updates, nullable_columns=nullable_columns)
    if wipe_updates:
        _execute_update(con, row_id=int(row["id"]), updates=wipe_updates)
        stats = MigrationStats(scanned=stats.scanned, backfilled=stats.backfilled, wiped=stats.wiped + 1)
    return stats


def _build_backfill_updates(
    row: sqlite3.Row,
    protection: PacientesFieldProtection,
    con: sqlite3.Connection,
) -> dict[str, str | None]:
    updates: dict[str, str | None] = {}
    for field in _PROTECTED_FIELDS:
        if row[f"{field}_enc"] and row[f"{field}_hash"]:
            continue
        legacy_value = _legacy_value(con, row=row, field=field)
        encoded = protection.encode(field, legacy_value)
        if encoded.encrypted is None:
            continue
        if encoded.legacy != row[field]:
            updates[field] = encoded.legacy
        updates[f"{field}_enc"] = encoded.encrypted
        updates[f"{field}_hash"] = encoded.lookup_hash
    return updates


def _legacy_value(con: sqlite3.Connection, *, row: sqlite3.Row, field: str) -> str | None:
    value = row[field]
    if field == "documento" or value is None:
        return value
    pii_cipher = get_connection_pii_cipher(con)
    return pii_cipher.decrypt_optional(value) if pii_cipher else value


def _build_wipe_updates(
    *,
    row: sqlite3.Row,
    updates: dict[str, str | None],
    nullable_columns: set[str],
) -> dict[str, None]:
    wipe: dict[str, None] = {}
    for field in _PROTECTED_FIELDS:
        if field not in nullable_columns:
            continue
        encrypted_now = updates.get(f"{field}_enc") or row[f"{field}_enc"]
        hashed_now = updates.get(f"{field}_hash") or row[f"{field}_hash"]
        if encrypted_now and hashed_now and row[field] is not None:
            wipe[field] = None
    return wipe


def _nullable_columns(con: sqlite3.Connection) -> set[str]:
    rows = con.execute("PRAGMA table_info(pacientes)").fetchall()
    return {row["name"] for row in rows if int(row["notnull"]) == 0}


def _execute_update(con: sqlite3.Connection, *, row_id: int, updates: dict[str, str | None]) -> None:
    columns = list(updates.keys())
    assignments = ", ".join(f"{column} = ?" for column in columns)
    values = [updates[column] for column in columns]
    con.execute(f"UPDATE pacientes SET {assignments} WHERE id = ?", (*values, row_id))


def main() -> int:
    stats = run(parse_args())
    LOGGER.info("crypto_migration.stats", extra={"scanned": stats.scanned, "backfilled": stats.backfilled, "wiped": stats.wiped})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
