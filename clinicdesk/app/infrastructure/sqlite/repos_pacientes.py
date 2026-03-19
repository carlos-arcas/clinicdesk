from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.common.sensitive_field_canonicalization import canonicalize_for_lookup
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.id_utils import require_lastrowid, require_row_id
from clinicdesk.app.infrastructure.sqlite.pacientes.crud import (
    fetch_by_documento,
    insert_sql,
    create_payload,
    update_payload,
    update_sql,
)
from clinicdesk.app.infrastructure.sqlite.pacientes.csv_io import (
    export_csv as export_pacientes_csv,
    import_csv as import_pacientes_csv,
)
from clinicdesk.app.infrastructure.sqlite.pacientes.mapping import format_num_historia, row_to_model
from clinicdesk.app.infrastructure.sqlite.pacientes.pii import decrypt_optional, encrypt_optional
from clinicdesk.app.infrastructure.sqlite.pacientes.search import query_models, search_filters
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher


class PacientesRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._pii_cipher = get_connection_pii_cipher(connection)
        self._field_protection = PacientesFieldProtection(connection)

    def create(self, paciente: Paciente) -> int:
        paciente.validar()
        payload = create_payload(paciente, self._field_protection, self._encrypt)
        cur = self._con.execute(insert_sql(self._field_protection.enabled), payload)
        paciente_id = require_lastrowid(cur, context="PacientesRepository.create")
        self._con.execute(
            "UPDATE pacientes SET num_historia = ? WHERE id = ?",
            (format_num_historia(paciente_id), paciente_id),
        )
        self._con.commit()
        return paciente_id

    def update(self, paciente: Paciente) -> None:
        if not paciente.id:
            raise ValidationError("No se puede actualizar un paciente sin id.")
        paciente.validar()
        payload = update_payload(paciente, self._field_protection, self._encrypt)
        self._con.execute(update_sql(self._field_protection.enabled), (*payload, paciente.id))
        self._con.commit()

    def delete(self, paciente_id: int) -> None:
        self._con.execute("UPDATE pacientes SET activo = 0 WHERE id = ?", (paciente_id,))
        self._con.commit()

    def get_by_id(self, paciente_id: int) -> Optional[Paciente]:
        row = self._con.execute("SELECT * FROM pacientes WHERE id = ? AND activo = 1", (paciente_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_id_by_documento(self, tipo_documento: TipoDocumento | str, documento: str) -> Optional[int]:
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        row = fetch_by_documento(self._con, self._field_protection, tipo=tipo, documento=documento)
        return require_row_id(row, context="PacientesRepository.get_id_by_documento") if row else None

    def get_id_by_email(self, email: str) -> Optional[int]:
        return self._get_id_by_contacto("email", email)

    def get_id_by_telefono(self, telefono: str) -> Optional[int]:
        return self._get_id_by_contacto("telefono", telefono)

    def list_all(self, *, solo_activos: bool = True) -> List[Paciente]:
        sql = "SELECT * FROM pacientes" + (" WHERE activo = 1" if solo_activos else "")
        sql += " ORDER BY apellidos, nombre"
        return query_models(self._con, sql, [], self._row_to_model, "PacientesRepository.list_all")

    def search(
        self,
        *,
        texto: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Paciente]:
        clauses, params = search_filters(
            field_protection=self._field_protection,
            texto=normalize_search_text(texto),
            tipo_documento=normalize_search_text(tipo_documento.value if tipo_documento else None),
            documento=normalize_search_text(documento),
            activo=activo,
        )
        sql = "SELECT * FROM pacientes"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre"
        return query_models(self._con, sql, params, self._row_to_model, "PacientesRepository.search")

    def export_csv(self, path: Path, pacientes: Iterable[Paciente]) -> None:
        export_pacientes_csv(path, pacientes)

    def import_csv(self, path: Path) -> int:
        return import_pacientes_csv(path, self.create)

    def _row_to_model(self, row: sqlite3.Row) -> Paciente:
        return row_to_model(row, field_protection=self._field_protection, decryptor=self._decrypt)

    def _encrypt(self, value: str | None) -> str | None:
        return encrypt_optional(self._pii_cipher, value)

    def _decrypt(self, value: str | None) -> str | None:
        return decrypt_optional(self._pii_cipher, value)

    def _get_id_by_contacto(self, field: str, value: str) -> Optional[int]:
        canonical = canonicalize_for_lookup(field, value)
        if canonical is None:
            return None
        if self._field_protection.enabled:
            row = self._con.execute(
                f"SELECT id FROM pacientes WHERE {field}_hash = ? AND activo = 1",
                (self._field_protection.hash_for_lookup(field, canonical),),
            ).fetchone()
            return require_row_id(row, context=f"PacientesRepository._get_id_by_contacto.{field}") if row else None
        if field == "email":
            row = self._con.execute(
                "SELECT id FROM pacientes WHERE LOWER(TRIM(COALESCE(email, ''))) = ? AND activo = 1",
                (canonical,),
            ).fetchone()
            return require_row_id(row, context=f"PacientesRepository._get_id_by_contacto.{field}") if row else None
        row = self._con.execute(
            "SELECT id FROM pacientes WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(COALESCE(telefono, '')), ' ', ''), '-', ''), '.', ''), '(', ''), ')', '') = ?",
            (canonical.lstrip("+"),),
        ).fetchone()
        return require_row_id(row, context=f"PacientesRepository._get_id_by_contacto.{field}") if row else None
