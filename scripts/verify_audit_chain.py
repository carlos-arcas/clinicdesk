from __future__ import annotations

import logging
import os
import sqlite3

from clinicdesk.app.infrastructure.sqlite.auditoria_integridad import verificar_cadena

LOGGER = logging.getLogger(__name__)


def _db_path() -> str:
    return os.environ.get("CLINICDESK_DB_PATH", "data/clinicdesk.sqlite")


def main() -> int:
    try:
        with sqlite3.connect(_db_path()) as con:
            con.row_factory = sqlite3.Row
            resultado = verificar_cadena(con)
    except sqlite3.Error:
        LOGGER.error("verify_audit_chain_db_error")
        return 2

    if resultado.ok:
        LOGGER.info("verify_audit_chain_ok")
        return 0

    LOGGER.error(
        "verify_audit_chain_fail",
        extra={"tabla": resultado.tabla, "primer_fallo_id": resultado.primer_fallo_id},
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
