from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite.pacientes.crud import (
    create_payload,
    fetch_by_documento,
    insert_sql,
    update_payload,
    update_sql,
)
from clinicdesk.app.infrastructure.sqlite.pacientes.csv_io import (
    export_csv as export_pacientes_csv,
)
from clinicdesk.app.infrastructure.sqlite.pacientes.csv_io import (
    import_csv as import_pacientes_csv,
)
from clinicdesk.app.infrastructure.sqlite.pacientes.mapping import format_num_historia, row_to_model
from clinicdesk.app.infrastructure.sqlite.pacientes.pii import decrypt_optional, encrypt_optional
from clinicdesk.app.infrastructure.sqlite.pacientes.search import query_models, search_filters
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher


LOGGER = get_logger(__name__)


class PiiProtectionPolicyError(RuntimeError):
    def __init__(self, message: str, *, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class PacientesRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._pii_cipher = get_connection_pii_cipher(connection)
        self._field_protection = PacientesFieldProtection(connection)

    def create(self, paciente: Paciente) -> int:
        paciente.validar()
        use_field_crypto = self._enforce_crypto_policy_for_write(operacion="create")
        payload = create_payload(
            paciente,
            self._field_protection,
            self._encrypt,
            use_field_crypto=use_field_crypto,
        )
        cur = self._con.execute(insert_sql(use_field_crypto), payload)
        paciente_id = int(cur.lastrowid)
        self._con.execute(
            "UPDATE pacientes SET num_historia = ? WHERE id = ?",
            (format_num_historia(paciente_id), paciente_id),
        )
        self._registrar_auditoria_pii(accion="PACIENTE_CREATE", paciente_id=paciente_id)
        self._con.commit()
        return paciente_id

    def update(self, paciente: Paciente) -> None:
        if not paciente.id:
            raise ValidationError("No se puede actualizar un paciente sin id.")
        paciente.validar()
        use_field_crypto = self._enforce_crypto_policy_for_write(operacion="update")
        payload = update_payload(
            paciente,
            self._field_protection,
            self._encrypt,
            use_field_crypto=use_field_crypto,
        )
        self._con.execute(update_sql(use_field_crypto), (*payload, paciente.id))
        self._registrar_auditoria_pii(accion="PACIENTE_UPDATE", paciente_id=paciente.id)
        self._con.commit()

    def delete(self, paciente_id: int) -> None:
        self._con.execute("UPDATE pacientes SET activo = 0 WHERE id = ?", (paciente_id,))
        self._con.commit()

    def get_by_id(self, paciente_id: int) -> Optional[Paciente]:
        row = self._con.execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_id_by_documento(self, tipo_documento: TipoDocumento | str, documento: str) -> Optional[int]:
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        row = fetch_by_documento(
            self._con,
            self._field_protection,
            tipo=tipo,
            documento=documento,
            lookup_hash=self._hash_lookup("documento", documento),
        )
        return int(row["id"]) if row else None

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
        telefono: Optional[str] = None,
        email: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Paciente]:
        clauses, params = search_filters(
            field_protection=self._field_protection,
            texto=normalize_search_text(texto),
            tipo_documento=normalize_search_text(tipo_documento.value if tipo_documento else None),
            documento=normalize_search_text(documento),
            telefono=normalize_search_text(telefono),
            email=normalize_search_text(email),
            documento_hash=self._hash_lookup("documento", documento),
            telefono_hash=self._hash_lookup("telefono", telefono),
            email_hash=self._hash_lookup("email", email),
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

    def _enforce_crypto_policy_for_write(self, *, operacion: str) -> bool:
        if not self._field_protection.enabled:
            return False
        if self._crypto_key_configured():
            return True
        if self._allow_plaintext_demo():
            LOGGER.warning(
                "AUDIT paciente_write_plaintext_demo",
                extra={
                    "action": "AUDIT",
                    "reason_code": "pii_plaintext_demo_mode",
                    "entity": "pacientes",
                    "operation": operacion,
                },
            )
            return False
        raise PiiProtectionPolicyError(
            "Falta CLINICDESK_CRYPTO_KEY para proteger PII de pacientes. "
            "Define la clave o habilita CLINICDESK_ALLOW_PII_PLAINTEXT_DEMO=1 solo en demo.",
            reason_code="missing_crypto_key",
        )

    @staticmethod
    def _allow_plaintext_demo() -> bool:
        raw = os.getenv("CLINICDESK_ALLOW_PII_PLAINTEXT_DEMO", "0").strip().lower()
        return raw in {"1", "true", "yes", "on"}

    @staticmethod
    def _crypto_key_configured() -> bool:
        return bool(os.getenv("CLINICDESK_CRYPTO_KEY", "").strip())

    def _hash_lookup(self, field: str, valor: str | None) -> str | None:
        if valor is None:
            return None
        if self._field_protection.enabled and not self._crypto_key_configured():
            if self._allow_plaintext_demo():
                return None
            raise PiiProtectionPolicyError(
                "Falta CLINICDESK_CRYPTO_KEY para búsquedas hash de pacientes.",
                reason_code="missing_crypto_key",
            )
        return self._field_protection.hash_for_lookup(field, valor)

    def _registrar_auditoria_pii(self, *, accion: str, paciente_id: int) -> None:
        paciente_id_hash = hashlib.sha256(str(paciente_id).encode("utf-8")).hexdigest()[:16]
        LOGGER.info(
            "AUDIT paciente pii write",
            extra={
                "action": accion,
                "paciente_id": paciente_id,
                "paciente_id_hash": paciente_id_hash,
            },
        )
