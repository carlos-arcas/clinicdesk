from __future__ import annotations

import sqlite3


def simular_tampering_privilegiado_sqlite(
    con: sqlite3.Connection,
    *,
    trigger_no_update: str,
    sentencia_update: str,
    parametros: tuple[object, ...] = (),
) -> None:
    """Simula manipulación privilegiada/out-of-band en escenarios append-only de tests.

    Este helper existe solo para tests de integridad. No representa el flujo normal de
    escritura ni relaja las garantías productivas de append-only.
    """

    con.execute(f"DROP TRIGGER IF EXISTS {trigger_no_update}")
    con.execute(sentencia_update, parametros)
    con.commit()
