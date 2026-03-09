from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable

GENESIS_HASH = "GENESIS"


@dataclass(frozen=True, slots=True)
class ResultadoVerificacionCadena:
    ok: bool
    tabla: str | None = None
    primer_fallo_id: int | None = None


def canonicalizar_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def calcular_entry_hash(prev_hash: str, payload: dict[str, Any]) -> str:
    base = f"{prev_hash}{canonicalizar_payload(payload)}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def ensure_auditoria_integridad_schema(con: sqlite3.Connection) -> None:
    _ensure_tabla_cadena(con, "auditoria_eventos", _payload_desde_fila_evento)
    _ensure_tabla_cadena(con, "auditoria_accesos", _payload_desde_fila_acceso)


def ensure_telemetria_integridad_schema(con: sqlite3.Connection) -> None:
    _ensure_tabla_cadena(
        con,
        "telemetria_eventos",
        _payload_desde_fila_telemetria,
        proteger_append_only=True,
    )


def siguiente_hash_evento(con: sqlite3.Connection, payload: dict[str, Any]) -> tuple[str, str]:
    return _siguiente_hash_para_tabla(con, "auditoria_eventos", payload)


def siguiente_hash_acceso(con: sqlite3.Connection, payload: dict[str, Any]) -> tuple[str, str]:
    return _siguiente_hash_para_tabla(con, "auditoria_accesos", payload)


def verificar_cadena(con: sqlite3.Connection) -> ResultadoVerificacionCadena:
    resultado_eventos = _verificar_tabla(con, "auditoria_eventos", _payload_desde_fila_evento)
    if not resultado_eventos.ok:
        return resultado_eventos
    return _verificar_tabla(con, "auditoria_accesos", _payload_desde_fila_acceso)


def siguiente_hash_telemetria(con: sqlite3.Connection, payload: dict[str, Any]) -> tuple[str, str]:
    return _siguiente_hash_para_tabla(con, "telemetria_eventos", payload)


def verificar_cadena_telemetria(con: sqlite3.Connection) -> ResultadoVerificacionCadena:
    ensure_telemetria_integridad_schema(con)
    return _verificar_tabla(con, "telemetria_eventos", _payload_desde_fila_telemetria)


def _ensure_tabla_cadena(
    con: sqlite3.Connection,
    tabla: str,
    construir_payload: Callable[[sqlite3.Row], dict[str, Any]],
    *,
    proteger_append_only: bool = False,
) -> None:
    columnas = {row["name"] for row in con.execute(f"PRAGMA table_info({tabla})").fetchall()}
    if "prev_hash" not in columnas:
        con.execute(f"ALTER TABLE {tabla} ADD COLUMN prev_hash TEXT")
    if "entry_hash" not in columnas:
        con.execute(f"ALTER TABLE {tabla} ADD COLUMN entry_hash TEXT NOT NULL DEFAULT ''")
    con.execute(f"CREATE INDEX IF NOT EXISTS idx_{tabla}_entry_hash ON {tabla}(entry_hash)")

    if not _tabla_requiere_backfill(con, tabla):
        return

    if proteger_append_only:
        _rehash_tabla_respetando_append_only(con, tabla, construir_payload)
        return

    _rehash_tabla(con, tabla, construir_payload)


def _tabla_requiere_backfill(con: sqlite3.Connection, tabla: str) -> bool:
    fila = con.execute(
        f"""
        SELECT id
        FROM {tabla}
        WHERE prev_hash IS NULL
           OR entry_hash IS NULL
           OR entry_hash = ''
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()
    return fila is not None


def _rehash_tabla_respetando_append_only(
    con: sqlite3.Connection,
    tabla: str,
    construir_payload: Callable[[sqlite3.Row], dict[str, Any]],
) -> None:
    trigger_update = f"trg_{tabla}_no_update"
    trigger_delete = f"trg_{tabla}_no_delete"
    con.execute(f"DROP TRIGGER IF EXISTS {trigger_update}")
    con.execute(f"DROP TRIGGER IF EXISTS {trigger_delete}")
    try:
        _rehash_tabla(con, tabla, construir_payload)
    finally:
        con.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_update}
            BEFORE UPDATE ON {tabla}
            BEGIN
                SELECT RAISE(ABORT, '{tabla}_append_only');
            END;
            """
        )
        con.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_delete}
            BEFORE DELETE ON {tabla}
            BEGIN
                SELECT RAISE(ABORT, '{tabla}_append_only');
            END;
            """
        )


def _rehash_tabla(
    con: sqlite3.Connection,
    tabla: str,
    construir_payload: Callable[[sqlite3.Row], dict[str, Any]],
) -> None:
    filas = con.execute(f"SELECT * FROM {tabla} ORDER BY id ASC").fetchall()
    prev_hash = GENESIS_HASH
    for fila in filas:
        entry_hash = calcular_entry_hash(prev_hash, construir_payload(fila))
        con.execute(
            f"UPDATE {tabla} SET prev_hash = ?, entry_hash = ? WHERE id = ?",
            (prev_hash, entry_hash, fila["id"]),
        )
        prev_hash = entry_hash


def _siguiente_hash_para_tabla(
    con: sqlite3.Connection,
    tabla: str,
    payload: dict[str, Any],
) -> tuple[str, str]:
    fila = con.execute(f"SELECT entry_hash FROM {tabla} ORDER BY id DESC LIMIT 1").fetchone()
    prev_hash = fila["entry_hash"] if fila and fila["entry_hash"] else GENESIS_HASH
    return prev_hash, calcular_entry_hash(prev_hash, payload)


def _verificar_tabla(
    con: sqlite3.Connection,
    tabla: str,
    construir_payload: Callable[[sqlite3.Row], dict[str, Any]],
) -> ResultadoVerificacionCadena:
    filas = con.execute(f"SELECT * FROM {tabla} ORDER BY id ASC").fetchall()
    prev_hash_esperado = GENESIS_HASH
    for fila in filas:
        entry_hash_esperado = calcular_entry_hash(prev_hash_esperado, construir_payload(fila))
        if fila["prev_hash"] != prev_hash_esperado or fila["entry_hash"] != entry_hash_esperado:
            return ResultadoVerificacionCadena(ok=False, tabla=tabla, primer_fallo_id=fila["id"])
        prev_hash_esperado = entry_hash_esperado
    return ResultadoVerificacionCadena(ok=True)


def _payload_desde_fila_evento(fila: sqlite3.Row) -> dict[str, Any]:
    return {
        "timestamp_utc": fila["timestamp_utc"],
        "action": fila["action"],
        "outcome": fila["outcome"],
        "actor_username": fila["actor_username"],
        "actor_role": fila["actor_role"],
        "correlation_id": fila["correlation_id"],
        "metadata_json": fila["metadata_json"],
    }


def _payload_desde_fila_acceso(fila: sqlite3.Row) -> dict[str, Any]:
    return {
        "timestamp_utc": fila["timestamp_utc"],
        "usuario": fila["usuario"],
        "modo_demo": fila["modo_demo"],
        "accion": fila["accion"],
        "entidad_tipo": fila["entidad_tipo"],
        "entidad_id": fila["entidad_id"],
        "metadata_json": fila["metadata_json"],
        "created_at_utc": fila["created_at_utc"],
    }


def _payload_desde_fila_telemetria(fila: sqlite3.Row) -> dict[str, Any]:
    return {
        "timestamp_utc": fila["timestamp_utc"],
        "usuario": fila["usuario"],
        "modo_demo": fila["modo_demo"],
        "evento": fila["evento"],
        "contexto": fila["contexto"],
        "entidad_tipo": fila["entidad_tipo"],
        "entidad_id": fila["entidad_id"],
    }
