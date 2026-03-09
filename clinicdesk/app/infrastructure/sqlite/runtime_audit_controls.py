from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EstadoAppendOnlyTabla:
    tabla: str
    aplica: bool
    ok: bool
    detalle: str


def verificar_append_only_tabla(con: sqlite3.Connection, tabla: str) -> EstadoAppendOnlyTabla:
    if not _tabla_existe(con, tabla):
        return EstadoAppendOnlyTabla(
            tabla=tabla,
            aplica=False,
            ok=False,
            detalle=f"tabla {tabla} no existe",
        )

    trigger_update = f"trg_{tabla}_no_update"
    trigger_delete = f"trg_{tabla}_no_delete"
    update_existe = _trigger_existe(con, trigger_update)
    delete_existe = _trigger_existe(con, trigger_delete)

    if update_existe and delete_existe:
        return EstadoAppendOnlyTabla(
            tabla=tabla,
            aplica=True,
            ok=True,
            detalle="append-only activo",
        )

    if not update_existe and not delete_existe:
        return EstadoAppendOnlyTabla(
            tabla=tabla,
            aplica=False,
            ok=False,
            detalle="sin politica append-only declarada en schema runtime",
        )

    faltantes: list[str] = []
    if not update_existe:
        faltantes.append(trigger_update)
    if not delete_existe:
        faltantes.append(trigger_delete)

    return EstadoAppendOnlyTabla(
        tabla=tabla,
        aplica=True,
        ok=False,
        detalle=f"faltan triggers: {', '.join(faltantes)}",
    )


def _tabla_existe(con: sqlite3.Connection, tabla: str) -> bool:
    fila = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
        (tabla,),
    ).fetchone()
    return fila is not None


def _trigger_existe(con: sqlite3.Connection, trigger_name: str) -> bool:
    fila = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'trigger' AND name = ? LIMIT 1",
        (trigger_name,),
    ).fetchone()
    return fila is not None
