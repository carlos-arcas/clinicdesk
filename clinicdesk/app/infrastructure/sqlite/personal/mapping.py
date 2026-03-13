from __future__ import annotations

import sqlite3
from typing import Callable

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.infrastructure.sqlite.date_utils import parse_iso_date
from clinicdesk.app.infrastructure.sqlite.personal_field_protection import PersonalFieldProtection


def row_to_model(
    row: sqlite3.Row,
    *,
    field_protection: PersonalFieldProtection,
    decryptor: Callable[[str | None], str | None],
) -> Personal:
    return Personal(
        id=row["id"],
        tipo_documento=TipoDocumento(row["tipo_documento"]),
        documento=decode(field_protection, "documento", row["documento"], row_value(row, "documento_enc")) or "",
        nombre=row["nombre"],
        apellidos=row["apellidos"],
        telefono=decode(field_protection, "telefono", decryptor(row["telefono"]), row_value(row, "telefono_enc")),
        email=decode(field_protection, "email", decryptor(row["email"]), row_value(row, "email_enc")),
        fecha_nacimiento=parse_iso_date(row["fecha_nacimiento"]),
        direccion=decode(field_protection, "direccion", decryptor(row["direccion"]), row_value(row, "direccion_enc")),
        activo=bool(row["activo"]),
        puesto=row["puesto"],
        turno=row["turno"],
    )


def row_value(row: sqlite3.Row, column: str) -> str | None:
    return row[column] if column in row.keys() else None


def decode(
    protection: PersonalFieldProtection,
    field: str,
    legacy: str | None,
    encrypted: str | None,
) -> str | None:
    return protection.decode(field, legacy=legacy, encrypted=encrypted)
