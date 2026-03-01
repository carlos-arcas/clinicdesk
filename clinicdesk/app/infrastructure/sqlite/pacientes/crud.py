from __future__ import annotations

import sqlite3

from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection


def insert_sql(protected: bool) -> str:
    if not protected:
        return (
            "INSERT INTO pacientes (tipo_documento, documento, nombre, apellidos, telefono, email, "
            "fecha_nacimiento, direccion, activo, num_historia, alergias, observaciones) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
    return (
        "INSERT INTO pacientes (tipo_documento, documento, documento_enc, documento_hash, nombre, apellidos, "
        "telefono, telefono_enc, telefono_hash, email, email_enc, email_hash, fecha_nacimiento, direccion, "
        "direccion_enc, direccion_hash, activo, num_historia, alergias, observaciones) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )


def update_sql(protected: bool) -> str:
    if not protected:
        return (
            "UPDATE pacientes SET tipo_documento = ?, documento = ?, nombre = ?, apellidos = ?, telefono = ?, email = ?, "
            "fecha_nacimiento = ?, direccion = ?, activo = ?, alergias = ?, observaciones = ? WHERE id = ?"
        )
    return (
        "UPDATE pacientes SET tipo_documento = ?, documento = ?, documento_enc = ?, documento_hash = ?, nombre = ?, apellidos = ?, "
        "telefono = ?, telefono_enc = ?, telefono_hash = ?, email = ?, email_enc = ?, email_hash = ?, fecha_nacimiento = ?, "
        "direccion = ?, direccion_enc = ?, direccion_hash = ?, activo = ?, alergias = ?, observaciones = ? WHERE id = ?"
    )


def create_payload(
    paciente: Paciente,
    protection: PacientesFieldProtection,
    encryptor,
) -> tuple[object, ...]:
    payload = _common_payload(paciente, protection, encryptor)
    return (*payload, None, encryptor(paciente.alergias), encryptor(paciente.observaciones))


def update_payload(
    paciente: Paciente,
    protection: PacientesFieldProtection,
    encryptor,
) -> tuple[object, ...]:
    payload = _common_payload(paciente, protection, encryptor)
    return (*payload, encryptor(paciente.alergias), encryptor(paciente.observaciones))


def _common_payload(
    paciente: Paciente,
    protection: PacientesFieldProtection,
    encryptor,
) -> tuple[object, ...]:
    if not protection.enabled:
        return (
            paciente.tipo_documento.value,
            paciente.documento,
            paciente.nombre,
            paciente.apellidos,
            encryptor(paciente.telefono),
            encryptor(paciente.email),
            format_iso_date(paciente.fecha_nacimiento),
            encryptor(paciente.direccion),
            int(paciente.activo),
        )

    documento = protection.encode("documento", paciente.documento)
    telefono = protection.encode("telefono", paciente.telefono)
    email = protection.encode("email", paciente.email)
    direccion = protection.encode("direccion", paciente.direccion)
    return (
        paciente.tipo_documento.value,
        documento.legacy,
        documento.encrypted,
        documento.lookup_hash,
        paciente.nombre,
        paciente.apellidos,
        encryptor(telefono.legacy),
        telefono.encrypted,
        telefono.lookup_hash,
        encryptor(email.legacy),
        email.encrypted,
        email.lookup_hash,
        format_iso_date(paciente.fecha_nacimiento),
        encryptor(direccion.legacy),
        direccion.encrypted,
        direccion.lookup_hash,
        int(paciente.activo),
    )


def fetch_by_documento(
    con: sqlite3.Connection,
    protection: PacientesFieldProtection,
    *,
    tipo: str,
    documento: str,
) -> sqlite3.Row | None:
    if protection.enabled:
        return con.execute(
            "SELECT id FROM pacientes WHERE tipo_documento = ? AND documento_hash = ?",
            (tipo, protection.hash_for_lookup("documento", documento)),
        ).fetchone()
    return con.execute(
        "SELECT id FROM pacientes WHERE tipo_documento = ? AND documento = ?",
        (tipo, documento),
    ).fetchone()
