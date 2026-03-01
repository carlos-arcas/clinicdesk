from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from clinicdesk.app.infrastructure.sqlite import db
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher

REQUIRED_CONFIRMATION = "WIPE-LEGACY"


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


@dataclass(frozen=True)
class MigrationConfig:
    table: str
    id_field: str
    fields: tuple[str, ...]
    wipe_policy: str


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def validate_options(options: MigrationOptions, *, required_confirmation: str = REQUIRED_CONFIRMATION) -> None:
    if not options.wipe_legacy:
        return
    if options.confirm_wipe != required_confirmation:
        raise ValueError("--wipe-legacy requiere --confirm-wipe WIPE-LEGACY")
    ensure_data_path(options.db_path)


def ensure_data_path(db_path: Path) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    data_root = (repo_root / "data").resolve()
    resolved_db = db_path.resolve()
    if data_root not in resolved_db.parents and resolved_db != data_root:
        raise ValueError("--wipe-legacy solo permitido para bases dentro de ./data")


def run(
    options: MigrationOptions,
    *,
    logger: logging.Logger,
    config: MigrationConfig,
    protection_factory: Callable[[sqlite3.Connection], object],
) -> MigrationStats:
    configure_logging()
    validate_options(options)
    con = db.bootstrap(options.db_path, options.schema_path, apply=True)
    try:
        return migrate_connection(
            con,
            wipe_legacy=options.wipe_legacy,
            logger=logger,
            config=config,
            protection_factory=protection_factory,
        )
    finally:
        con.close()


def migrate_connection(
    con: sqlite3.Connection,
    *,
    wipe_legacy: bool,
    logger: logging.Logger,
    config: MigrationConfig,
    protection_factory: Callable[[sqlite3.Connection], object],
) -> MigrationStats:
    protection = protection_factory(con)
    if not protection.has_columns:
        raise RuntimeError(f"La tabla {config.table} no tiene columnas *_enc/_hash")
    if not protection.enabled:
        raise RuntimeError("CLINICDESK_FIELD_CRYPTO=1 y CLINICDESK_CRYPTO_KEY son obligatorios")

    rows = con.execute(f"SELECT * FROM {config.table}").fetchall()
    nullable_columns = nullable_columns_for_table(con, config.table)
    stats = MigrationStats(scanned=len(rows))
    for row in rows:
        stats = migrate_row(
            con,
            row=row,
            protection=protection,
            wipe_legacy=wipe_legacy,
            nullable_columns=nullable_columns,
            config=config,
            stats=stats,
        )
    con.commit()
    logger.info("crypto_migration.completed", extra=stats.__dict__)
    return stats


def migrate_row(
    con: sqlite3.Connection,
    *,
    row: sqlite3.Row,
    protection: object,
    wipe_legacy: bool,
    nullable_columns: set[str],
    config: MigrationConfig,
    stats: MigrationStats,
) -> MigrationStats:
    row_id = int(row[config.id_field])
    backfill_updates = build_backfill_updates(row, protection, con, config.fields)
    backfilled = stats.backfilled + int(bool(backfill_updates))
    if backfill_updates:
        execute_update(con, table=config.table, id_field=config.id_field, row_id=row_id, updates=backfill_updates)

    wiped = stats.wiped
    if wipe_legacy:
        wipe_updates = build_wipe_updates(
            row=row,
            backfill_updates=backfill_updates,
            nullable_columns=nullable_columns,
            fields=config.fields,
            wipe_policy=config.wipe_policy,
        )
        wiped += int(bool(wipe_updates))
        if wipe_updates:
            execute_update(con, table=config.table, id_field=config.id_field, row_id=row_id, updates=wipe_updates)
    return MigrationStats(scanned=stats.scanned, backfilled=backfilled, wiped=wiped)


def build_backfill_updates(
    row: sqlite3.Row,
    protection: object,
    con: sqlite3.Connection,
    fields: tuple[str, ...],
) -> dict[str, str | None]:
    updates: dict[str, str | None] = {}
    for field in fields:
        if row[f"{field}_enc"] and row[f"{field}_hash"]:
            continue
        legacy_value = legacy_value_for_backfill(con, row=row, field=field)
        encoded = protection.encode(field, legacy_value)
        if encoded.encrypted is None:
            continue
        if field == "documento" and encoded.legacy != row[field]:
            updates[field] = encoded.legacy
        updates[f"{field}_enc"] = encoded.encrypted
        updates[f"{field}_hash"] = encoded.lookup_hash
    return updates


def legacy_value_for_backfill(con: sqlite3.Connection, *, row: sqlite3.Row, field: str) -> str | None:
    value = row[field]
    if field == "documento" or value is None:
        return value
    pii_cipher = get_connection_pii_cipher(con)
    return pii_cipher.decrypt_optional(value) if pii_cipher else value


def build_wipe_updates(
    *,
    row: sqlite3.Row,
    backfill_updates: dict[str, str | None],
    nullable_columns: set[str],
    fields: tuple[str, ...],
    wipe_policy: str,
) -> dict[str, None]:
    if wipe_policy != "nullable_only":
        raise ValueError(f"wipe_policy no soportada: {wipe_policy}")
    wipe: dict[str, None] = {}
    for field in fields:
        if field not in nullable_columns:
            continue
        encrypted_now = backfill_updates.get(f"{field}_enc") or row[f"{field}_enc"]
        hashed_now = backfill_updates.get(f"{field}_hash") or row[f"{field}_hash"]
        if encrypted_now and hashed_now and row[field] not in (None, ""):
            wipe[field] = None
    return wipe


def nullable_columns_for_table(con: sqlite3.Connection, table: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows if int(row["notnull"]) == 0}


def execute_update(
    con: sqlite3.Connection,
    *,
    table: str,
    id_field: str,
    row_id: int,
    updates: dict[str, str | None],
) -> None:
    columns = list(updates.keys())
    assignments = ", ".join(f"{column} = ?" for column in columns)
    values = [updates[column] for column in columns]
    con.execute(f"UPDATE {table} SET {assignments} WHERE {id_field} = ?", (*values, row_id))
