# infrastructure/sqlite/repos_personal.py
from __future__ import annotations

import sqlite3
from typing import Optional

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.infrastructure.sqlite.id_utils import require_lastrowid, require_row_id
from clinicdesk.app.infrastructure.sqlite.personal.crud import (
    create_payload,
    fetch_by_documento,
    insert_sql,
    update_sql,
)
from clinicdesk.app.infrastructure.sqlite.personal.mapping import row_to_model
from clinicdesk.app.infrastructure.sqlite.personal.search import query_models, search_filters
from clinicdesk.app.infrastructure.sqlite.personal_field_protection import PersonalFieldProtection
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher


class PersonalRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._pii_cipher = get_connection_pii_cipher(connection)
        self._field_protection = PersonalFieldProtection(connection)

    def create(self, personal: Personal) -> int:
        personal.validar()
        payload = create_payload(personal, self._field_protection, self._encrypt)
        cur = self._con.execute(insert_sql(self._field_protection.enabled), payload)
        self._con.commit()
        return require_lastrowid(cur, context="PersonalRepository.create")

    def update(self, personal: Personal) -> None:
        if not personal.id:
            raise ValidationError("No se puede actualizar personal sin id.")
        personal.validar()
        payload = create_payload(personal, self._field_protection, self._encrypt)
        self._con.execute(update_sql(self._field_protection.enabled), (*payload, personal.id))
        self._con.commit()

    def delete(self, personal_id: int) -> None:
        self._con.execute("UPDATE personal SET activo = 0 WHERE id = ?", (personal_id,))
        self._con.commit()

    def get_by_id(self, personal_id: int) -> Optional[Personal]:
        row = self._con.execute(
            "SELECT * FROM personal WHERE id = ? AND activo = 1",
            (personal_id,),
        ).fetchone()
        return self._row_to_model(row) if row else None

    def get_id_by_documento(self, tipo_documento: TipoDocumento | str, documento: str) -> Optional[int]:
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        row = fetch_by_documento(self._con, self._field_protection, tipo=tipo, documento=documento)
        return require_row_id(row, context="PersonalRepository.get_id_by_documento") if row else None

    def get_id_by_nombre(self, nombre: str, apellidos: Optional[str] = None) -> Optional[int]:
        nombre = normalize_search_text(nombre)
        apellidos = normalize_search_text(apellidos)
        if not nombre:
            return None
        clauses = ["nombre LIKE ? COLLATE NOCASE", "activo = 1"]
        params: list[object] = [like_value(nombre)]
        if apellidos:
            clauses.append("apellidos LIKE ? COLLATE NOCASE")
            params.append(like_value(apellidos))
        sql = "SELECT id FROM personal WHERE " + " AND ".join(clauses) + " ORDER BY apellidos, nombre"
        row = self._con.execute(sql, params).fetchone()
        return require_row_id(row, context="PersonalRepository.get_id_by_nombre") if row else None

    def list_all(self, *, solo_activos: bool = True) -> list[Personal]:
        sql = "SELECT * FROM personal" + (" WHERE activo = 1" if solo_activos else "")
        sql += " ORDER BY apellidos, nombre"
        return query_models(self._con, sql, [], self._row_to_model, "PersonalRepository.list_all")

    def search(
        self,
        *,
        texto: Optional[str] = None,
        puesto: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> list[Personal]:
        clauses, params = search_filters(
            field_protection=self._field_protection,
            texto=normalize_search_text(texto),
            puesto=normalize_search_text(puesto),
            tipo_documento=normalize_search_text(tipo_documento.value if tipo_documento else None),
            documento=normalize_search_text(documento),
            activo=activo,
        )
        sql = "SELECT * FROM personal"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre"
        return query_models(self._con, sql, params, self._row_to_model, "PersonalRepository.search")

    def _row_to_model(self, row: sqlite3.Row) -> Personal:
        return row_to_model(row, field_protection=self._field_protection, decryptor=self._decrypt)

    def _encrypt(self, value: str | None) -> str | None:
        return self._pii_cipher.encrypt_optional(value) if self._pii_cipher else value

    def _decrypt(self, value: str | None) -> str | None:
        return self._pii_cipher.decrypt_optional(value) if self._pii_cipher else value
