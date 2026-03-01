from __future__ import annotations

import sqlite3

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.date_utils import parse_iso_date
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection


def row_to_model(
    row: sqlite3.Row,
    *,
    field_protection: PacientesFieldProtection,
    decryptor,
) -> Paciente:
    return Paciente(
        id=row["id"],
        tipo_documento=TipoDocumento(row["tipo_documento"]),
        documento=_decode(field_protection, "documento", row["documento"], row_value(row, "documento_enc")) or "",
        nombre=row["nombre"],
        apellidos=row["apellidos"],
        telefono=_decode(field_protection, "telefono", decryptor(row["telefono"]), row_value(row, "telefono_enc")),
        email=_decode(field_protection, "email", decryptor(row["email"]), row_value(row, "email_enc")),
        fecha_nacimiento=parse_iso_date(row["fecha_nacimiento"]),
        direccion=_decode(field_protection, "direccion", decryptor(row["direccion"]), row_value(row, "direccion_enc")),
        activo=bool(row["activo"]),
        num_historia=row["num_historia"],
        alergias=decryptor(row["alergias"]),
        observaciones=decryptor(row["observaciones"]),
    )


def row_value(row: sqlite3.Row, column: str) -> str | None:
    return row[column] if column in row.keys() else None


def format_num_historia(paciente_id: int) -> str:
    return f"HIST-{paciente_id:04d}"


def _decode(
    protection: PacientesFieldProtection,
    field: str,
    legacy: str | None,
    encrypted: str | None,
) -> str | None:
    return protection.decode(field, legacy=legacy, encrypted=encrypted)
