from __future__ import annotations

import logging
import sqlite3
from typing import List

from clinicdesk.app.common.search_utils import like_value
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection

logger = logging.getLogger(__name__)


def search_filters(
    *,
    field_protection: PacientesFieldProtection,
    texto: str | None,
    tipo_documento: str | None,
    documento: str | None,
    activo: bool | None,
) -> tuple[list[str], list[object]]:
    clauses: list[str] = []
    params: list[object] = []

    if texto:
        _append_text_filter(clauses, params, texto, field_protection.enabled)

    if tipo_documento:
        clauses.append("tipo_documento LIKE ? COLLATE NOCASE")
        params.append(like_value(tipo_documento))

    if documento:
        if field_protection.enabled:
            clauses.append("documento_hash = ?")
            params.append(field_protection.hash_for_lookup("documento", documento))
        else:
            clauses.append("documento LIKE ? COLLATE NOCASE")
            params.append(like_value(documento))

    if activo is not None:
        clauses.append("activo = ?")
        params.append(int(activo))

    return clauses, params


def query_models(con: sqlite3.Connection, sql: str, params: list[object], mapper, context: str) -> List:
    try:
        rows = con.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        logger.error("Error SQL en %s: %s", context, exc)
        return []
    return [mapper(row) for row in rows]


def _append_text_filter(clauses: list[str], params: list[object], texto: str, protected: bool) -> None:
    like = like_value(texto)
    if protected:
        clauses.append("(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE)")
        params.extend([like, like])
        return
    clauses.append(
        "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE "
        "OR documento LIKE ? COLLATE NOCASE)"
    )
    params.extend([like, like, like])
