from __future__ import annotations

import sqlite3

from clinicdesk.app.common.field_crypto_flags import pacientes_field_crypto_enabled
from clinicdesk.app.common.field_protection_base import FieldProtectionBase, ProtectedFieldValue


class PacientesFieldProtection(FieldProtectionBase):
    def __init__(self, connection: sqlite3.Connection) -> None:
        super().__init__(
            connection,
            table_name="pacientes",
            fields=("documento", "email", "telefono", "direccion"),
            fields_not_null_legacy=("documento",),
            enabled_flag=pacientes_field_crypto_enabled(),
        )


__all__ = ["PacientesFieldProtection", "ProtectedFieldValue"]
