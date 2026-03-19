from __future__ import annotations

import sqlite3
from typing import Callable

from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date
from clinicdesk.app.infrastructure.sqlite.personal_field_protection import PersonalFieldProtection


def insert_sql(protected: bool) -> str:
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


def update_sql(protected: bool) -> str:
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


def create_payload(
    personal: Personal,
    protection: PersonalFieldProtection,
    encryptor: Callable[[str | None], str | None],
) -> tuple[object, ...]:
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


def fetch_by_documento(
    con: sqlite3.Connection,
    protection: PersonalFieldProtection,
    *,
    tipo: str,
    documento: str,
) -> sqlite3.Row | None:
    if protection.enabled:
        return con.execute(
            "SELECT id FROM personal WHERE tipo_documento = ? AND documento_hash = ? AND activo = 1",
            (tipo, protection.hash_for_lookup("documento", documento)),
        ).fetchone()
    return con.execute(
        "SELECT id FROM personal WHERE tipo_documento = ? AND documento = ? AND activo = 1",
        (tipo, documento),
    ).fetchone()
