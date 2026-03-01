# infrastructure/sqlite/repos_personal.py
from __future__ import annotations

import logging
import sqlite3
from typing import List, Optional

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date, parse_iso_date
from clinicdesk.app.infrastructure.sqlite.personal_field_protection import PersonalFieldProtection
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher

logger = logging.getLogger(__name__)


class PersonalRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._pii_cipher = get_connection_pii_cipher(connection)
        self._field_protection = PersonalFieldProtection(connection)

    def create(self, personal: Personal) -> int:
        personal.validar()
        payload = _payload_for_write(personal, self._field_protection, self._encrypt)
        cur = self._con.execute(_insert_sql(self._field_protection.enabled), payload)
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, personal: Personal) -> None:
        if not personal.id:
            raise ValidationError("No se puede actualizar personal sin id.")
        personal.validar()
        payload = _payload_for_write(personal, self._field_protection, self._encrypt)
        self._con.execute(_update_sql(self._field_protection.enabled), (*payload, personal.id))
        self._con.commit()

    def delete(self, personal_id: int) -> None:
        self._con.execute("UPDATE personal SET activo = 0 WHERE id = ?", (personal_id,))
        self._con.commit()

    def get_by_id(self, personal_id: int) -> Optional[Personal]:
        row = self._con.execute("SELECT * FROM personal WHERE id = ?", (personal_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_id_by_documento(self, tipo_documento: TipoDocumento | str, documento: str) -> Optional[int]:
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        row = _fetch_by_documento(self._con, self._field_protection, tipo=tipo, documento=documento)
        return int(row["id"]) if row else None

    def get_id_by_nombre(self, nombre: str, apellidos: Optional[str] = None) -> Optional[int]:
        nombre = normalize_search_text(nombre)
        apellidos = normalize_search_text(apellidos)
        if not nombre:
            return None
        clauses = ["nombre LIKE ? COLLATE NOCASE"]
        params: list[object] = [like_value(nombre)]
        if apellidos:
            clauses.append("apellidos LIKE ? COLLATE NOCASE")
            params.append(like_value(apellidos))
        sql = "SELECT id FROM personal WHERE " + " AND ".join(clauses) + " ORDER BY apellidos, nombre"
        row = self._con.execute(sql, params).fetchone()
        return int(row["id"]) if row else None

    def list_all(self, *, solo_activos: bool = True) -> List[Personal]:
        sql = "SELECT * FROM personal" + (" WHERE activo = 1" if solo_activos else "")
        sql += " ORDER BY apellidos, nombre"
        return _query_models(self._con, sql, [], self._row_to_model, "PersonalRepository.list_all")

    def search(
        self,
        *,
        texto: Optional[str] = None,
        puesto: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Personal]:
        clauses, params = _search_filters(
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
        return _query_models(self._con, sql, params, self._row_to_model, "PersonalRepository.search")

    def _row_to_model(self, row: sqlite3.Row) -> Personal:
        return Personal(
            id=row["id"],
            tipo_documento=TipoDocumento(row["tipo_documento"]),
            documento=_decode(self._field_protection, "documento", row["documento"], _row_value(row, "documento_enc")) or "",
            nombre=row["nombre"],
            apellidos=row["apellidos"],
            telefono=_decode(self._field_protection, "telefono", self._decrypt(row["telefono"]), _row_value(row, "telefono_enc")),
            email=_decode(self._field_protection, "email", self._decrypt(row["email"]), _row_value(row, "email_enc")),
            fecha_nacimiento=parse_iso_date(row["fecha_nacimiento"]),
            direccion=_decode(self._field_protection, "direccion", self._decrypt(row["direccion"]), _row_value(row, "direccion_enc")),
            activo=bool(row["activo"]),
            puesto=row["puesto"],
            turno=row["turno"],
        )

    def _encrypt(self, value: str | None) -> str | None:
        return self._pii_cipher.encrypt_optional(value) if self._pii_cipher else value

    def _decrypt(self, value: str | None) -> str | None:
        return self._pii_cipher.decrypt_optional(value) if self._pii_cipher else value


def _insert_sql(protected: bool) -> str:
    if not protected:
        return (
            "INSERT INTO personal (tipo_documento, documento, nombre, apellidos, telefono, email, "
            "fecha_nacimiento, direccion, activo, puesto, turno) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
    return (
        "INSERT INTO personal (tipo_documento, documento, documento_enc, documento_hash, nombre, apellidos, "
        "telefono, telefono_enc, telefono_hash, email, email_enc, email_hash, fecha_nacimiento, direccion, "
        "direccion_enc, direccion_hash, activo, puesto, turno) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )


def _update_sql(protected: bool) -> str:
    if not protected:
        return (
            "UPDATE personal SET tipo_documento = ?, documento = ?, nombre = ?, apellidos = ?, telefono = ?, email = ?, "
            "fecha_nacimiento = ?, direccion = ?, activo = ?, puesto = ?, turno = ? WHERE id = ?"
        )
    return (
        "UPDATE personal SET tipo_documento = ?, documento = ?, documento_enc = ?, documento_hash = ?, nombre = ?, apellidos = ?, "
        "telefono = ?, telefono_enc = ?, telefono_hash = ?, email = ?, email_enc = ?, email_hash = ?, fecha_nacimiento = ?, "
        "direccion = ?, direccion_enc = ?, direccion_hash = ?, activo = ?, puesto = ?, turno = ? WHERE id = ?"
    )


def _payload_for_write(personal: Personal, protection: PersonalFieldProtection, encryptor) -> tuple[object, ...]:
    if not protection.enabled:
        return (
            personal.tipo_documento.value,
            personal.documento,
            personal.nombre,
            personal.apellidos,
            encryptor(personal.telefono),
            encryptor(personal.email),
            format_iso_date(personal.fecha_nacimiento),
            encryptor(personal.direccion),
            int(personal.activo),
            personal.puesto,
            personal.turno,
        )
    documento = protection.encode("documento", personal.documento)
    telefono = protection.encode("telefono", personal.telefono)
    email = protection.encode("email", personal.email)
    direccion = protection.encode("direccion", personal.direccion)
    return (
        personal.tipo_documento.value,
        documento.legacy,
        documento.encrypted,
        documento.lookup_hash,
        personal.nombre,
        personal.apellidos,
        encryptor(telefono.legacy),
        telefono.encrypted,
        telefono.lookup_hash,
        encryptor(email.legacy),
        email.encrypted,
        email.lookup_hash,
        format_iso_date(personal.fecha_nacimiento),
        encryptor(direccion.legacy),
        direccion.encrypted,
        direccion.lookup_hash,
        int(personal.activo),
        personal.puesto,
        personal.turno,
    )


def _fetch_by_documento(
    con: sqlite3.Connection,
    protection: PersonalFieldProtection,
    *,
    tipo: str,
    documento: str,
) -> sqlite3.Row | None:
    if protection.enabled:
        return con.execute(
            "SELECT id FROM personal WHERE tipo_documento = ? AND documento_hash = ?",
            (tipo, protection.hash_for_lookup("documento", documento)),
        ).fetchone()
    return con.execute(
        "SELECT id FROM personal WHERE tipo_documento = ? AND documento = ?",
        (tipo, documento),
    ).fetchone()


def _search_filters(
    *,
    field_protection: PersonalFieldProtection,
    texto: str | None,
    puesto: str | None,
    tipo_documento: str | None,
    documento: str | None,
    activo: bool | None,
) -> tuple[list[str], list[object]]:
    clauses: list[str] = []
    params: list[object] = []
    if texto:
        _append_text_filter(clauses, params, texto, field_protection.enabled)
    if puesto:
        clauses.append("puesto LIKE ? COLLATE NOCASE")
        params.append(like_value(puesto))
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


def _append_text_filter(clauses: list[str], params: list[object], texto: str, protected: bool) -> None:
    like = like_value(texto)
    if protected:
        clauses.append("(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE OR puesto LIKE ? COLLATE NOCASE)")
        params.extend([like, like, like])
        return
    clauses.append(
        "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE OR documento LIKE ? COLLATE NOCASE "
        "OR telefono LIKE ? COLLATE NOCASE OR puesto LIKE ? COLLATE NOCASE)"
    )
    params.extend([like, like, like, like, like])


def _query_models(con: sqlite3.Connection, sql: str, params: list[object], mapper, context: str) -> List[Personal]:
    try:
        rows = con.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        logger.error("Error SQL en %s: %s", context, exc)
        return []
    return [mapper(row) for row in rows]


def _row_value(row: sqlite3.Row, column: str) -> str | None:
    return row[column] if column in row.keys() else None


def _decode(protection: PersonalFieldProtection, field: str, legacy: str | None, encrypted: str | None) -> str | None:
    return protection.decode(field, legacy=legacy, encrypted=encrypted)
