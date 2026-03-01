from __future__ import annotations

import argparse
import logging
import sqlite3
from pathlib import Path

from clinicdesk.app.infrastructure.sqlite.personal_field_protection import PersonalFieldProtection
from scripts.crypto_migrate_common import (
    MigrationConfig,
    MigrationOptions,
    MigrationStats,
    migrate_connection,
    run as common_run,
    validate_options,
)

LOGGER = logging.getLogger("scripts.crypto_migrate_personal")
_CONFIG = MigrationConfig(
    table="personal",
    id_field="id",
    fields=("documento", "telefono", "email", "direccion"),
    wipe_policy="nullable_only",
)


def parse_args() -> MigrationOptions:
    parser = argparse.ArgumentParser(description="Backfill seguro de cifrado por campo en personal")
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
    return common_run(options, logger=LOGGER, config=_CONFIG, protection_factory=PersonalFieldProtection)


def _validate_options(options: MigrationOptions) -> None:
    validate_options(options)


def _migrate(con: sqlite3.Connection, wipe_legacy: bool) -> MigrationStats:
    return migrate_connection(
        con,
        wipe_legacy=wipe_legacy,
        logger=LOGGER,
        config=_CONFIG,
        protection_factory=PersonalFieldProtection,
    )


def main() -> int:
    stats = run(parse_args())
    LOGGER.info("crypto_migration.stats", extra=stats.__dict__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
